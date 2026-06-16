# -*- coding: utf-8 -*-
"""
Mongeze Logistics Platform - Core Backend Intelligent Module
============================================================
Developed for: Eng. Ahmed Mostafa (Founder & CTO)
Role: Senior AI Lead & Solutions Architect

This module implements the core secure logistics operational logic:
1. Real-time Firebase Firestore & Storage configuration (Streamlit secrets & .env fallbacks).
2. Strict PII anonymity checks: Masking sensitive customer and driver contact data
   until the order status changes to "Accepted".
3. Transactional Firebase Order Creation and Acceptance workflows.
4. Comprehensive Order Cancellation and Driver Withdrawal system with strict reasons logging.
5. Real-time Async Firestore Chat Listening support for Mutimodal messages (Text, Vision, Audio).

This file is clean, production-ready, highly secure, and optimized for GitHub.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore

# Configure secure and structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] MongezeAI-Core: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MongezeBackend")


# =====================================================================
# 1️⃣ SAFE FIREBASE INITIALIZATION & SECURITY ENVIRONMENT MANAGEMENT
# =====================================================================
def get_firebase_db() -> firestore.client:
    """
    Initializes and returns a secure connection to the Firebase Firestore Client.
    Safely utilizes Streamlit secrets (st.secrets) or environment variables (.env).
    """
    # Check if Firebase application is already initialized to avoid duplicate initialization errors
    if not firebase_admin._apps:
        # Check Strategy A: Standard Streamlit Secrets Object
        try:
            import streamlit as st
            if "firebase" in st.secrets:
                logger.info("Initializing Firebase Admin SDK using Streamlit Secrets.")
                firebase_secrets = dict(st.secrets["firebase"])
                cred = credentials.Certificate(firebase_secrets)
                firebase_admin.initialize_app(cred)
                return firestore.client()
        except ImportError:
            logger.debug("Streamlit not found on runtime classpath. Moving to environment variable retrieval.")
        except Exception as e:
            logger.warning(f"Failed to initialize via Streamlit secrets: {e}. Trying Environment/JSON variables.")

        # Check Strategy B: Certificate file path or Service Account JSON via environment variable
        env_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        env_credentials_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

        if env_credentials_path and os.path.exists(env_credentials_path):
            logger.info(f"Initializing Firebase Admin using path credentials: {env_credentials_path}")
            cred = credentials.Certificate(env_credentials_path)
            firebase_admin.initialize_app(cred)
        elif env_credentials_json:
            logger.info("Initializing Firebase Admin using raw JSON environment payload.")
            import json
            service_account_info = json.loads(env_credentials_json)
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        else:
            # Check Strategy C: Fallback to application default credentials
            logger.warning("No explicit service credentials found. Initializing with default Application Credentials.")
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            except Exception as default_err:
                logger.error(f"Failed to load application default credentials: {default_err}")
                raise RuntimeError(
                    "CRITICAL: Unable to provision Firebase credentials. "
                    "Ensure GOOGLE_APPLICATION_CREDENTIALS is set, Streamlit secrets are active, "
                    "or package configuration is correct."
                )

    return firestore.client()


# Try loading the default Firestore client for this instance
try:
    db = get_firebase_db()
    logger.info("Successfully established connection to Mongeze Live Firestore instance.")
except Exception as initialization_error:
    logger.error(f"Firestore initialization aborted: {initialization_error}")
    db = None


# =====================================================================
# 2️⃣ PII DATA OBFUSCATION AND COMPLIANCE GUARD (PRIVACY PROTECTION)
# =====================================================================
def mask_order_privacy(order_data: Dict[str, Any], viewer_id: str, viewer_role: str) -> Dict[str, Any]:
    """
    Ensures strict privacy standards for clients and drivers (GDPR and Local Compliance).
    Renders phone numbers, email addresses, and private contact lines 'Hidden (مخفي حتى قبول الطلب)'
    unless the order status is officially marked as 'Accepted' (قيد التوصيل).
    
    Rules:
    - If status is 'Accepted', both the client and driver can see each other's details.
    - If viewer is the owner of the details (e.g. Client viewing client details), they can always see their own details.
    - System/Admin role can always see all unmasked data.
    """
    masked_order = order_data.copy()
    status = masked_order.get("status", "Pending")
    
    # Check if the transaction is unlocked (Accepted represents order execution mode)
    is_unlocked = (status.lower() in ["accepted", "ongoing", "arrived", "completed"])
    
    # Client compliance masking
    client_id = masked_order.get("client_id")
    if not is_unlocked and viewer_role != "system" and viewer_id != client_id:
        if "client_phone" in masked_order:
            masked_order["client_phone"] = "Hidden (مخفي حتى قبول الكابتن للطلب)"
        if "client_email" in masked_order:
            masked_order["client_email"] = "Hidden (مخفي للحماية)"
            
    # Driver compliance masking
    driver_id = masked_order.get("driver_id")
    if not is_unlocked and viewer_role != "system" and viewer_id != driver_id:
        if "driver_phone" in masked_order:
            masked_order["driver_phone"] = "Hidden (مخفي حتى تأكيد الشحنة)"
        if "driver_email" in masked_order:
            masked_order["driver_email"] = "Hidden (مخفي للحماية)"

    return masked_order


# =====================================================================
# 3️⃣ DISPATCH MECHANICS: TRIP CREATION & ACCEPTANCE WORKFLOWS
# =====================================================================
def create_order(
    client_id: str,
    client_name: str,
    client_phone: str,
    client_email: str,
    pickup_location: Dict[str, float],   # e.g. {"lat": 30.044, "lon": 31.235}
    dropoff_location: Dict[str, float],  # e.g. {"lat": 30.013, "lon": 31.208}
    cargo_type: str,                     # 'fragile', 'standard', 'heavy'
    cargo_weight_kg: float,
    fare_amount: float,
    currency: str = "EGP"
) -> str:
    """
    Creates a new logistics delivery trip tracking document in Firestore.
    The order initiates in "Pending" status with client details encapsulated securely.
    """
    if not db:
        raise RuntimeError("Database connection not active.")
        
    order_ref = db.collection("orders").document()
    order_id = order_ref.id
    
    order_payload = {
        "order_id": order_id,
        "client_id": client_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "client_email": client_email,
        "pickup_location": pickup_location,
        "dropoff_location": dropoff_location,
        "status": "Pending",
        "cargo_details": {
            "cargo_type": cargo_type,
            "cargo_weight_kg": cargo_weight_kg,
            "remarks": "إنشاء حزمة الطلب بنجاح عبر النظام الرقمي"
        },
        "financials": {
            "fare_amount": fare_amount,
            "currency": currency,
            "payment_status": "Unpaid"
        },
        "driver_id": None,
        "driver_name": None,
        "driver_phone": None,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "historical_logs": [
            {
                "event": "order_created",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "تم إنشاء طلب التوصيل وهو بانتظار قبول أنسب مندوب."
            }
        ]
    }
    
    order_ref.set(order_payload)
    logger.info(f"Successfully dispatched order ORD-{order_id} on Firebase. Status: Pending.")
    return order_id


def accept_order(
    order_id: str,
    driver_id: str,
    driver_name: str,
    driver_phone: str,
    driver_email: str
) -> Dict[str, Any]:
    """
    Executes a transactional block to allocate the driver, change order status to 'Accepted',
    and synchronously instantiate the secure Real-Time Chat Room (chat_rooms) linked to the trip.
    """
    if not db:
        raise RuntimeError("Database connection not active.")
        
    order_ref = db.collection("orders").document(order_id)
    room_ref = db.collection("chat_rooms").document(f"room_{order_id}")
    
    # Transactional execution loop to verify order is still available
    @firestore.transactional
    def update_in_transaction(transaction):
        snapshot = order_ref.get(transaction=transaction)
        if not snapshot.exists:
            raise ValueError(f"Order ORD-{order_id} does not exist.")
            
        current_data = snapshot.to_dict()
        if current_data.get("status") != "Pending":
            raise ValueError(f"Order ORD-{order_id} has already been claimed or cancelled. Status: {current_data.get('status')}")
            
        # 1. Update trip order with driver allocation metrics
        historical_entry = {
            "event": "order_accepted",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": f"تم قبول الطلب بنجاح بواسطة الكابتن {driver_name}، وتفعيل تبادل الأرقام والتواصل الآن."
        }
        
        transaction.update(order_ref, {
            "status": "Accepted",
            "driver_id": driver_id,
            "driver_name": driver_name,
            "driver_phone": driver_phone,
            "driver_email": driver_email,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "historical_logs": firestore.ArrayUnion([historical_entry])
        })
        
        # 2. Setup the designated chat room document securely
        room_payload = {
            "room_id": f"room_{order_id}",
            "order_id": order_id,
            "client_id": current_data.get("client_id"),
            "driver_id": driver_id,
            "status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
            "last_message": {
                "text": "تم فتح قناة المحادثة والاتصال المباشر بين الكابتن والعميل بنجاح.",
                "sender_role": "system",
                "sent_at": firestore.SERVER_TIMESTAMP
            }
        }
        transaction.set(room_ref, room_payload)
        
        # 3. Create a welcoming system message in the chat room messages subcollection
        msg_ref = room_ref.collection("messages").document()
        msg_payload = {
            "message_id": msg_ref.id,
            "sender_id": "system_dispatcher",
            "sender_role": "system",
            "sender_name": "نظام التوزيع التلقائي منجز",
            "type": "text",
            "content": "تم تفعيل شات منجز الآمن. يمكنك الآن تبادل الصور، الرسائل الصوتية وتأكيدات المواقع مع الطرف الآخر.",
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        transaction.set(msg_ref, msg_payload)
        
        logger.info(f"Transaction committed: ORD-{order_id} with driver {driver_name}. ChatRoom: room_{order_id} is active.")
        
        # Retrieve the updated data
        current_data["status"] = "Accepted"
        current_data["driver_id"] = driver_id
        current_data["driver_name"] = driver_name
        current_data["driver_phone"] = driver_phone
        current_data["driver_email"] = driver_email
        return current_data

    transaction = db.transaction()
    updated_order = update_in_transaction(transaction)
    
    # Return unmasked details since status is now 'Accepted'
    return mask_order_privacy(updated_order, driver_id, "driver")


# =====================================================================
# 4️⃣ STRUCTURED ORDER CANCELLATION & WITHDRAWAL LOGIC
# =====================================================================

# Strict allowed withdrawal reason definitions to keep Firestore logs pristine
CLIENT_CANCELLATION_REASONS = {
    1: "تأخر السائق في الاستجابة أو الحضور",
    2: "تغيير في تفاصيل أو وجهة الطلب",
    3: "تمت تلبية الطلب بوسيلة أخرى",
    4: "أسباب شخصية / أخرى"
}

DRIVER_WITHDRAWAL_REASONS = {
    1: "المسافة إلى نقطة الاستلام بعيدة جداً",
    2: "عطل مفاجئ في المركبة (السيارة/الدراجة)",
    3: "صعوبة التواصل مع العميل",
    4: "حجم أو طبيعة الشحنة غير مطابقة للوصف"
}

def cancel_order(
    order_id: str,
    canceler_role: str,  # 'client' or 'driver'
    canceler_id: str,
    reason_code: int,
    additional_notes: str = ""
) -> bool:
    """
    Cancels an active or pending order. Registers the strict reason code translation key
    directly into Firestore records for logistics audit trails.
    """
    if not db:
        raise RuntimeError("Database connection not active.")
        
    order_ref = db.collection("orders").document(order_id)
    order_snap = order_ref.get()
    
    if not order_snap.exists:
        raise ValueError(f"Order ORD-{order_id} was not found on Firestore.")
        
    order_data = order_snap.to_dict()
    current_status = order_data.get("status", "Pending")
    
    if current_status in ["completed", "cancelled"]:
        raise ValueError(f"Cannot alter status. Order is already in a terminal state: {current_status}")

    # Validate and translate the reason code based on the initiator's role
    if canceler_role == "client":
        if reason_code not in CLIENT_CANCELLATION_REASONS:
            raise ValueError(f"Invalid Client cancellation code: {reason_code}. Must be 1, 2, 3, or 4.")
        translated_reason = CLIENT_CANCELLATION_REASONS[reason_code]
    elif canceler_role == "driver":
        if reason_code not in DRIVER_WITHDRAWAL_REASONS:
            raise ValueError(f"Invalid Driver withdrawal code: {reason_code}. Must be 1, 2, 3, or 4.")
        translated_reason = DRIVER_WITHDRAWAL_REASONS[reason_code]
    else:
        raise ValueError("Role must strictly be 'client' or 'driver'.")

    cancellation_stamp = datetime.utcnow().isoformat() + "Z"
    
    # Assembly of descriptive log item
    historical_entry = {
        "event": "order_cancelled",
        "timestamp": cancellation_stamp,
        "message": f"تم إلغاء الطلب بواسطة {canceler_role}. السبب: {translated_reason}. تفاصيل إضافية: {additional_notes}"
    }
    
    # Save the cancellation data atomically to Firestore
    order_ref.update({
        "status": "Cancelled",
        "cancellation_meta": {
            "cancelled_by_role": canceler_role,
            "canceler_id": canceler_id,
            "reason_code": reason_code,
            "reason_text": translated_reason,
            "additional_notes": additional_notes,
            "timestamp": cancellation_stamp
        },
        "updated_at": firestore.SERVER_TIMESTAMP,
        "historical_logs": firestore.ArrayUnion([historical_entry])
    })
    
    # Archive parent chat room if active to prevent further messaging leakage
    room_ref = db.collection("chat_rooms").document(f"room_{order_id}")
    if room_ref.get().exists:
        room_ref.update({
            "status": "closed",
            "last_message": {
                "text": f"تم إغلاق الغرفة نظراً لتوقف وإلغاء الرحلة: {translated_reason}",
                "sender_role": "system",
                "sent_at": firestore.SERVER_TIMESTAMP
            }
        })
        # Post cancellation notification inside the chat collection
        room_ref.collection("messages").document().set({
            "message_id": "cancellation_notice_" + order_id,
            "sender_id": "system_dispatcher",
            "sender_role": "system",
            "sender_name": "نظام الإلغاء الآمن",
            "type": "text",
            "content": f"تنبيه: تم إلغاء هذه الرحلة رسمياً بطلب من {canceler_role}. السبب المسجل: {translated_reason}",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
    logger.info(f"Order ORD-{order_id} cancellation logged successfully. Initiated by {canceler_role} to Firestore.")
    return True


# =====================================================================
# 5️⃣ MULTI-MODAL CHAT ENGINE & SNAPSHOT STREAM LISTENER
# =====================================================================
def send_chat_message(
    room_id: str,
    sender_id: str,
    sender_role: str,
    sender_name: str,
    message_type: str,  # 'text', 'image', 'voice'
    content: str,       # Message text or path/link references
    file_url: Optional[str] = None,
    metadata_payload: Optional[Dict[str, Any]] = None
) -> str:
    """
    Submits a message directly to Firestore subcollection.
    Message_type supports text, voice-notes, and cargo image verifications cleanly.
    """
    if not db:
        raise RuntimeError("Database connection not active.")
        
    room_ref = db.collection("chat_rooms").document(room_id)
    if not room_ref.get().exists:
        raise ValueError(f"Chat Room {room_id} does not exist.")
        
    msg_ref = room_ref.collection("messages").document()
    msg_id = msg_ref.id
    
    msg_data = {
        "message_id": msg_id,
        "sender_id": sender_id,
        "sender_role": sender_role,
        "sender_name": sender_name,
        "type": message_type,
        "content": content,
        "file_url": file_url,
        "metadata": metadata_payload or {},
        "timestamp": firestore.SERVER_TIMESTAMP
    }
    
    # Write atomicity (Write the message and update parent room's quick-check index concurrently)
    batch = db.batch()
    batch.set(msg_ref, msg_data)
    
    abbreviated_text = content[:100] if message_type == "text" else f"[{message_type.upper()} MEDIA]"
    batch.update(room_ref, {
        "last_message": {
            "text": abbreviated_text,
            "sender_role": sender_role,
            "sender_name": sender_name,
            "sent_at": firestore.SERVER_TIMESTAMP
        }
    })
    batch.commit()
    logger.info(f"Published Multi-Modal message ({message_type}) as {msg_id} on Room {room_id}.")
    return msg_id


def listen_to_chat_messages(room_id: str, callback: Callable[[List[Dict[str, Any]]], None]):
    """
    Starts an asynchronous real-time snap-stream listener for incoming client/driver correspondence.
    The callback function is triggered as soon as fresh records enter the Firestore subcollection.
    """
    if not db:
        raise RuntimeError("Database connection not active.")
        
    # Order query ascendingly by timestamp for clear messaging continuity
    messages_query = (
        db.collection("chat_rooms")
        .document(room_id)
        .collection("messages")
        .order_by("timestamp", direction=firestore.Query.ASCENDING)
    )
    
    def on_snapshot_triggered(doc_snapshot, changes, read_time):
        messages_list = []
        for doc in doc_snapshot:
            data = doc.to_dict()
            # Convert ServerTimestamp to iso strings safely if ready
            if data.get("timestamp"):
                try:
                    data["timestamp"] = data["timestamp"].isoformat()
                except AttributeError:
                    data["timestamp"] = str(data["timestamp"])
            messages_list.append(data)
            
        logger.info(f"Live-Stream Callback triggered. Count of fetched texts: {len(messages_list)}")
        callback(messages_list)

    # Begin the Firestore on_snapshot listener thread
    listener_watch = messages_query.on_snapshot(on_snapshot_triggered)
    logger.info(f"Real-time stream listener active for Mongeze Chat Room: {room_id}")
    return listener_watch
