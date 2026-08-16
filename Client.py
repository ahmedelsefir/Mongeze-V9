"""
Client.py - Customer-facing views for the Monjez platform.
Contains: Parcels, Taxi, Customer Chat, and Customer Tracking views.
Refactored with Object-Oriented Principles (OOP), Flexible Signatures, and Streamlit-Safe Forms.
"""

import html
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import streamlit as st

logger = logging.getLogger(__name__)


# ==============================================================================
# 📦 1. DOMAIN MODELS (الكائنات الهيكلية للمشروع - OOP)
# ==============================================================================

@dataclass
class ParcelOrder:
    """كائن يمثل طلب الطرد ويحمل بياناته، وظائف التحقق، وتوليد البريد المنسق."""
    customer: str
    details: str
    price: float
    payment_method: str
    pickup_lat: float = 30.0444
    pickup_lon: float = 31.2357
    dest_lat: float = 30.0131
    dest_lon: float = 31.1089
    distance_km: Optional[float] = None
    time_min: Optional[float] = None
    order_id: str = field(default_factory=lambda: f"PRCL-{int(time.time())}")
    status: str = "Searching for Driver"
    driver: str = "Not Assigned"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def validate_payment(self, wallet_balance: float) -> tuple[bool, Optional[str]]:
        """دالة داخل الكائن للتحقق من سلامة عملية الدفع."""
        if self.payment_method == "👛 خصم من رصيد المحفظة":
            if wallet_balance < self.price:
                return False, f"❌ رصيد محفظتك ({wallet_balance:.2f} EGP) غير كافٍ. الرسوم المطلوبة: {self.price} EGP"
        return True, None

    def generate_html_email(self) -> str:
        """توليد فاتورة البريد الإلكتروني بلغة HTML وتنسيق احترافي للشحنات."""
        dist_info = f"{self.distance_km} كم | {self.time_min} دقيقة" if self.distance_km and self.time_min else "حسب المسار"
        return f"""
        <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #2e7d32; text-align: center;">📦 طلب طرد جديد - مُنجز</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h1 style="font-size: 32px; color: #333; text-align: center;">{self.price:.2f} ج.م.</h1>
                
                <div style="background: #f0f4f8; padding: 12px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>👤 العميل:</strong> {html.escape(self.customer)}</p>
                    <p style="margin: 5px 0;"><strong>📝 تفاصيل الشحنة والعنوان:</strong> {html.escape(self.details)}</p>
                    <p style="margin: 5px 0; color: #555;">⏱️ <strong>المسافة والزمن التقديري:</strong> {dist_info}</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="padding: 8px 0; color: #666;">طريقة الدفع:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.payment_method}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">رقم الطلب:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.order_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">تاريخ الطلب:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.timestamp}</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    def to_dict(self) -> Dict[str, Any]:
        """تحويل الكائن إلى قاموس جاهز للإرسال إلى Firebase."""
        return {
            "order_id": self.order_id,
            "type": "Parcel Delivery",
            "customer": self.customer,
            "details": self.details,
            "price": self.price,
            "status": self.status,
            "driver": self.driver,
            "customer_lat": self.pickup_lat,
            "customer_lon": self.pickup_lon,
            "dest_lat": self.dest_lat,
            "dest_lon": self.dest_lon,
            "estimated_distance_km": self.distance_km,
            "estimated_time_min": self.time_min,
            "payment_method": self.payment_method,
            "timestamp": self.timestamp
        }


@dataclass
class TaxiOrder:
    """كائن يمثل طلب التاكسي ويغلف تفاصيل الرحلة والتسعير وتوليد الفاتورة."""
    customer: str
    pickup_loc: str
    dest_loc: str
    price: float
    payment_method: str
    pickup_lat: float
    pickup_lon: float
    dest_lat: float
    dest_lon: float
    distance_km: Optional[float] = None
    time_min: Optional[float] = None
    surge_factor: float = 1.0
    order_id: str = field(default_factory=lambda: f"TAXI-{int(time.time())}")
    status: str = "Searching for Driver"
    driver: str = "Not Assigned"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def validate_payment(self, wallet_balance: float) -> tuple[bool, Optional[str]]:
        """دالة للتحقق من رصيد المحفظة للتاكسي."""
        if self.payment_method == "👛 خصم من رصيد المحفظة":
            if wallet_balance < self.price:
                return False, f"❌ رصيد محفظتك ({wallet_balance:.2f} EGP) غير كافٍ. الرسوم المطلوبة: {self.price} EGP"
        return True, None

    def generate_html_email(self) -> str:
        """توليد فاتورة البريد الإلكتروني بلغة HTML وتنسيق احترافي للرحلات."""
        dist_info = f"{self.distance_km} كم | {self.time_min} دقيقة" if self.distance_km and self.time_min else "غير محدد"
        surge_text = f" (رسوم الذروة x{self.surge_factor})" if self.surge_factor > 1.0 else ""
        return f"""
        <div style="font-family: Arial, sans-serif; direction: rtl; text-align: right; background-color: #f9f9f9; padding: 20px;">
            <div style="max-width: 500px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #1565c0; text-align: center;">🚕 طلب مشوار جديد - مُنجز</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                
                <h1 style="font-size: 32px; color: #333; text-align: center;">{self.price:.2f} ج.م.{surge_text}</h1>
                
                <div style="background: #f0f4f8; padding: 12px; border-radius: 8px; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>👤 الراكب:</strong> {html.escape(self.customer)}</p>
                    <p style="margin: 5px 0;"><strong>📍 نقطة الانطلاق:</strong> {html.escape(self.pickup_loc)}</p>
                    <p style="margin: 5px 0;"><strong>🏁 الوجهة:</strong> {html.escape(self.dest_loc)}</p>
                    <p style="margin: 5px 0; color: #555;">⏱️ <strong>المسافة والزمن التقديري:</strong> {dist_info}</p>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="padding: 8px 0; color: #666;">طريقة الدفع:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.payment_method}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">رقم الطلب:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.order_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #666;">تاريخ الطلب:</td>
                        <td style="padding: 8px 0; text-align: left; font-weight: bold;">{self.timestamp}</td>
                    </tr>
                </table>
            </div>
        </div>
        """

    def to_dict(self) -> Dict[str, Any]:
        """تحويل كائن التاكسي إلى قاموس لـ Firebase."""
        return {
            "order_id": self.order_id,
            "type": "Taxi Ride",
            "customer": self.customer,
            "from": self.pickup_loc,
            "to": self.dest_loc,
            "price": self.price,
            "status": self.status,
            "driver": self.driver,
            "customer_lat": self.pickup_lat,
            "customer_lon": self.pickup_lon,
            "dest_lat": self.dest_lat,
            "dest_lon": self.dest_lon,
            "estimated_distance_km": self.distance_km,
            "estimated_time_min": self.time_min,
            "surge_factor": self.surge_factor,
            "payment_method": self.payment_method,
            "timestamp": self.timestamp
        }


# ==============================================================================
# 🎨 2. CUSTOMER VIEWS (شاشات العميل بواجهة Streamlit)
# ==============================================================================

def render_parcels_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert,
                       fetch_user_settings=None, initiate_wallet_topup=None, **kwargs):
    """Render the parcels ordering page with flexible **kwargs to prevent TypeError."""
    st.markdown("## 📦 Parcel Shipment Center")
    
    # جلب رصيد المحفظة
    user_wallet = 0.0
    if fetch_user_settings:
        try:
            user_data = fetch_user_settings(user_name)
            user_wallet = float(user_data.get("wallet_balance", 0.0)) if user_data else 0.0
        except Exception as e:
            logger.warning(f"Could not fetch wallet balance: {str(e)}")

    # عرض مربع الشحن خارج النموذج لتجنب StreamlitAPIException
    if st.session_state.get("show_parcel_topup", False):
        st.warning(f"⚠️ رصيدك منخفض ({user_wallet:.2f} EGP). هل تريد إضافة رصيد؟")
        col1, col2 = st.columns([1, 2])
        with col1:
            if initiate_wallet_topup and st.button("💳 إضافة رصيد الآن", key="topup_parcel_btn"):
                initiate_wallet_topup(user_name)
                st.session_state["show_parcel_topup"] = False
        with col2:
            if st.button("إلغاء ✖️", key="cancel_parcel_topup"):
                st.session_state["show_parcel_topup"] = False
                st.rerun()

    with st.form("parcel_v10"):
        details = st.text_area("Shipment Details & Pickup/Delivery Addresses:")
        
        with st.expander("📍 Location Coordinates (GPS) for Map Tracking", expanded=False):
            col_g1, col_g2, col_g3, col_g4 = st.columns(4)
            with col_g1:
                p_lat = st.number_input("Pickup Lat:", value=30.0444, format="%.4f", key="p_lat")
            with col_g2:
                p_lon = st.number_input("Pickup Lon:", value=31.2357, format="%.4f", key="p_lon")
            with col_g3:
                d_lat = st.number_input("Dest Lat:", value=30.0131, format="%.4f", key="d_lat")
            with col_g4:
                d_lon = st.number_input("Dest Lon:", value=31.1089, format="%.4f", key="d_lon")

        price = st.number_input("Estimated Budget (EGP):", min_value=10.0, value=70.0)
        
        st.divider()
        st.markdown("### 💳 Payment Method")
        payment_method = st.radio(
            "طريقة الدفع المفضلة:",
            ["💵 كاش (عند الوصول)", "👛 خصم من رصيد المحفظة", "💳 فيزا / أونلاين (Paymob)"],
            horizontal=False
        )
        
        if payment_method == "👛 خصم من رصيد المحفظة":
            st.info(f"💰 رصيد محفظتك الحالي: **{user_wallet:.2f} EGP**")
        
        if st.form_submit_button("🚀 Post Order to Network") and details.strip():
            order_obj = ParcelOrder(
                customer=user_name,
                details=details.strip(),
                price=price,
                payment_method=payment_method,
                pickup_lat=p_lat,
                pickup_lon=p_lon,
                dest_lat=d_lat,
                dest_lon=d_lon
            )
            
            is_valid, error_msg = order_obj.validate_payment(user_wallet)
            
            if not is_valid:
                st.error(error_msg)
            elif payment_method == "💳 فيزا / أونلاين (Paymob)" and user_wallet < price * 0.1:
                st.session_state["show_parcel_topup"] = True
                st.rerun()
            else:
                try:
                    payload = order_obj.to_dict()
                    if send_to_firebase("orders", payload):
                        st.session_state["my_active_order_id"] = order_obj.order_id
                        html_invoice = order_obj.generate_html_email()
                        send_system_email(f"New Parcel Order {order_obj.order_id}", html_invoice)
                        st.success(f"🎉 Order posted successfully! Tracking Code: {order_obj.order_id}")
                        if st.session_state.get("audio_notifications_enabled", False):
                            trigger_audio_alert()
                    else:
                        st.error("❌ Failed to post order. Please check your connection.")
                except Exception as e:
                    logger.error(f"Error creating parcel order: {str(e)}")
                    st.error(f"Error: {str(e)}")


def render_taxi_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert,
                     fetch_from_firebase=None, fetch_user_settings=None, initiate_wallet_topup=None, **kwargs):
    """Render the taxi ordering page with dynamic fare estimation and flexible **kwargs."""
    from pricing_engine import estimate_trip

    st.markdown("## 🚕 Taxi Ride Request Center")

    user_wallet = 0.0
    if fetch_user_settings:
        try:
            user_data = fetch_user_settings(user_name)
            user_wallet = float(user_data.get("wallet_balance", 0.0)) if user_data else 0.0
        except Exception as e:
            logger.warning(f"Could not fetch wallet balance: {str(e)}")

    active_orders_count = 0
    available_drivers_count = 0
    if fetch_from_firebase:
        try:
            orders = fetch_from_firebase("orders")
            active_orders_count = len([o for o in orders if o.get("status") == "Searching for Driver"]) if orders else 0
        except Exception as e:
            logger.warning(f"Could not fetch orders for surge calc: {str(e)}")

    # عرض مربع الشحن خارج النموذج لتجنب StreamlitAPIException
    if st.session_state.get("show_taxi_topup", False):
        st.warning(f"⚠️ رصيدك منخفض ({user_wallet:.2f} EGP). هل تريد إضافة رصيد؟")
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            if initiate_wallet_topup and st.button("💳 إضافة رصيد الآن", key="topup_taxi_outside"):
                initiate_wallet_topup(user_name)
                st.session_state["show_taxi_topup"] = False
        with col_t2:
            if st.button("إلغاء ✖️", key="cancel_topup_taxi"):
                st.session_state["show_taxi_topup"] = False
                st.rerun()

    with st.form("taxi_v10"):
        start = st.text_input("Pickup Location:")
        end = st.text_input("Destination:")

        col_gps1, col_gps2, col_gps3, col_gps4 = st.columns(4)
        with col_gps1:
            pickup_lat = st.number_input("Pickup Latitude:", value=30.0444, format="%.4f")
        with col_gps2:
            pickup_lon = st.number_input("Pickup Longitude:", value=31.2357, format="%.4f")
        with col_gps3:
            dest_lat = st.number_input("Destination Latitude:", value=30.0131, format="%.4f")
        with col_gps4:
            dest_lon = st.number_input("Destination Longitude:", value=31.1089, format="%.4f")

        estimate = estimate_trip(
            pickup_lat, pickup_lon, dest_lat, dest_lon,
            active_orders=active_orders_count,
            available_drivers=available_drivers_count,
        )
        if estimate:
            fare = estimate["fare"]
            surge_label = f"⚡ Surge x{estimate['surge_factor']}" if estimate["surge_factor"] > 1.0 else "✅ Normal rates"
            st.info(
                f"📍 Distance: **{estimate['distance_km']} km** | "
                f"⏱️ ETA: **{estimate['time_minutes']} min** | {surge_label}\n\n"
                f"💰 Base: {fare['base_fare']} + Distance: {fare['distance_cost']} + Time: {fare['time_cost']} "
                f"= {fare['subtotal']} → **Total: {fare['total_fare']} EGP**"
            )
            suggested_price = float(fare["total_fare"])
        else:
            st.warning("⚠️ Invalid coordinates — cannot estimate fare.")
            suggested_price = 120.0

        price = st.number_input("Offered Fare (EGP):", min_value=10.0, value=suggested_price)

        st.divider()
        st.markdown("### 💳 Payment Method")
        payment_method = st.radio(
            "طريقة الدفع المفضلة:",
            ["💵 كاش (عند الوصول)", "👛 خصم من رصيد المحفظة", "💳 فيزا / أونلاين (Paymob)"],
            horizontal=False,
            key="taxi_payment"
        )
        
        if payment_method == "👛 خصم من رصيد المحفظة":
            st.info(f"💰 رصيد محفظتك الحالي: **{user_wallet:.2f} EGP**")

        if st.form_submit_button("🚕 Post Ride to Network") and start.strip() and end.strip():
            taxi_obj = TaxiOrder(
                customer=user_name,
                pickup_loc=start.strip(),
                dest_loc=end.strip(),
                price=price,
                payment_method=payment_method,
                pickup_lat=float(pickup_lat),
                pickup_lon=float(pickup_lon),
                dest_lat=float(dest_lat),
                dest_lon=float(dest_lon),
                distance_km=estimate["distance_km"] if estimate else None,
                time_min=estimate["time_minutes"] if estimate else None,
                surge_factor=estimate["surge_factor"] if estimate else 1.0
            )

            is_valid, error_msg = taxi_obj.validate_payment(user_wallet)

            if not is_valid:
                st.error(error_msg)
            elif payment_method == "💳 فيزا / أونلاين (Paymob)" and user_wallet < price * 0.1:
                st.session_state["show_taxi_topup"] = True
                st.rerun()
            else:
                try:
                    payload = taxi_obj.to_dict()
                    if send_to_firebase("orders", payload):
                        st.session_state["my_active_order_id"] = taxi_obj.order_id
                        html_invoice = taxi_obj.generate_html_email()
                        send_system_email(f"New Taxi Request {taxi_obj.order_id}", html_invoice)
                        st.success(f"🎉 Ride posted successfully! Tracking Code: {taxi_obj.order_id}")
                        if st.session_state.get("audio_notifications_enabled", False):
                            trigger_audio_alert()
                    else:
                        st.error("❌ Failed to post ride. Please check your connection.")
                except Exception as e:
                    logger.error(f"Error creating taxi order: {str(e)}")
                    st.error(f"Error: {str(e)}")


# ==============================================================================
# 💬 3. CHAT & SUPPORT FUNCTIONS (دوال الدردشة والدعم الفني)
# ==============================================================================

def _extract_order_id_from_room(selected_room):
    """Extract order_id from room selection string."""
    try:
        if "Order Chat" in selected_room:
            part = selected_room.split("Order Chat")[1].strip()
            return part.split(" - ")[0].strip()
    except Exception:
        pass
    return None


def _find_order_by_id(orders, order_id):
    """Find an order dict from the orders list by order_id."""
    if not orders or not order_id:
        return None
    return next((o for o in orders if o.get("order_id") == order_id), None)


def render_chat_page(user_name, user_role, send_to_firebase, fetch_from_firebase,
                     update_firebase_node=None, log_accounting_entry=None,
                     fetch_firebase_raw=None, **kwargs):
    """Render the chat rooms page with flexible **kwargs."""
    st.markdown("## 💬 Live Chat & Unified Communication")
    try:
        orders = fetch_from_firebase("orders")
        room_options = ["Admin & Staff General Chat"]
        if orders:
            for o in orders:
                try:
                    room_options.append(f"Order Chat {o.get('order_id', 'unknown')} - Customer: {o.get('customer', 'unknown')}")
                except Exception as option_error:
                    logger.warning(f"Error building room option: {str(option_error)}")
                    continue

        selected_room = st.selectbox("🎯 Select Active Chat Channel:", room_options)
        clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")

        current_order_id = _extract_order_id_from_room(selected_room)
        current_order = _find_order_by_id(orders, current_order_id) if current_order_id else None
        is_order_room = current_order_id is not None

        if is_order_room:
            _render_chat_actions_menu(
                user_name=user_name,
                user_role=user_role,
                order_id=current_order_id,
                order_data=current_order,
                clean_room=clean_room,
                send_to_firebase=send_to_firebase,
                fetch_from_firebase=fetch_from_firebase,
                update_firebase_node=update_firebase_node,
                log_accounting_entry=log_accounting_entry,
            )
            _render_support_banner(current_order_id, fetch_firebase_raw)

        with st.form("chat_form_v10", clear_on_submit=True):
            msg_text = st.text_input("📝 Type your message:")
            if st.form_submit_button("💬 Send Message") and msg_text.strip():
                try:
                    send_to_firebase(f"private_chats/{clean_room}", {
                        "role": user_role, "sender": user_name, "message": msg_text.strip(),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    time.sleep(0.2)
                except Exception as chat_error:
                    logger.error(f"Error sending chat message: {str(chat_error)}")
                    st.error("❌ Failed to send message")

        try:
            chats = fetch_from_firebase(f"private_chats/{clean_room}")
            if chats and len(chats) > 0:
                for m in chats[-20:]:
                    try:
                        role_color = "#1E88E5" if m.get("role") == "Admin" else "#2ECC71" if m.get("role") == "Customer" else "#F1C40F"
                        st.markdown(f"""
                        <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 6px; border-right: 5px solid {role_color};'>
                            <span style='color: {role_color}; font-weight: bold;'>[{html.escape(str(m.get('role', 'Unknown')))}] {html.escape(str(m.get('sender', 'Unknown')))}</span> 
                            <span style='font-size: 0.75em; color: gray;'>({html.escape(str(m.get('timestamp', '')))})</span>: 
                            <p style='margin-top: 4px; font-size: 1.1em; color: black;'>{html.escape(str(m.get('message', '')))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as msg_error:
                        logger.warning(f"Error rendering message: {str(msg_error)}")
                        continue
        except Exception as chat_fetch_error:
            logger.error(f"Error fetching chat messages: {str(chat_fetch_error)}")
            st.warning("⚠️ Error loading messages")
    except Exception as e:
        logger.error(f"Error in chat page: {str(e)}")
        st.error("Error loading chat page")


def _render_chat_actions_menu(user_name, user_role, order_id, order_data,
                              clean_room, send_to_firebase, fetch_from_firebase,
                              update_firebase_node, log_accounting_entry):
    """Render the three-dot contextual menu at the top of the chat box."""
    try:
        order_status = order_data.get("status", "") if order_data else ""
        is_cancelled = order_status == "Cancelled"

        with st.popover("⋮ More Options", use_container_width=False):
            st.markdown(f"**🔖 Order:** `{order_id}`")
            if order_status:
                st.caption(f"Current Status: {order_status}")
            st.divider()

            st.markdown("##### ❌ Cancel Order")
            if is_cancelled:
                st.info("This order is already cancelled.")
            else:
                st.warning("⚠️ Are you sure you want to cancel this order? This action cannot be undone.")
                if st.button("🗑️ Confirm Cancellation", key="confirm_cancel_order",
                             type="primary", use_container_width=True):
                    _handle_cancel_order(
                        user_name=user_name,
                        user_role=user_role,
                        order_id=order_id,
                        order_data=order_data,
                        clean_room=clean_room,
                        send_to_firebase=send_to_firebase,
                        update_firebase_node=update_firebase_node,
                        log_accounting_entry=log_accounting_entry,
                    )

            st.divider()

            st.markdown("##### 🚨 Request Support")
            st.caption("Opens an immediate support channel and notifies the admin team.")
            if st.button("📞 Call Support Now", key="request_support", use_container_width=True):
                _handle_request_support(
                    user_name=user_name,
                    user_role=user_role,
                    order_id=order_id,
                    clean_room=clean_room,
                    send_to_firebase=send_to_firebase,
                    update_firebase_node=update_firebase_node,
                )
    except Exception as e:
        logger.error(f"Error rendering chat actions menu: {str(e)}")
        st.error("⚠️ Error loading options menu")


def _handle_cancel_order(user_name, user_role, order_id, order_data,
                         clean_room, send_to_firebase, update_firebase_node,
                         log_accounting_entry):
    """Process order cancellation: update Firebase, log ledger, close chat."""
    try:
        db_id = order_data.get("db_id") if order_data else None
        if not db_id:
            st.error("❌ Cannot find order data in database.")
            return

        if update_firebase_node:
            success = update_firebase_node(f"orders/{db_id}", {
                "status": "Cancelled",
                "cancelled_by": user_name,
                "cancelled_role": user_role,
                "cancelled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            if not success:
                st.error("❌ Failed to update order status. Please try again.")
                return
        else:
            st.warning("⚠️ Database update service is currently unavailable.")
            return

        if log_accounting_entry:
            log_accounting_entry(order_id, {
                "event": "order_cancelled",
                "cancelled_by": user_name,
                "cancelled_role": user_role,
                "original_price": order_data.get("price", 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Cancelled from chat",
            })

        try:
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": "System",
                "sender": "⚙️ System",
                "message": f"❌ Order {order_id} has been cancelled by {user_name} ({user_role})",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post cancellation chat message: {str(msg_err)}")

        if st.session_state.get("my_active_order_id") == order_id:
            st.session_state["my_active_order_id"] = None

        st.success(f"Order {order_id} has been cancelled successfully.")
        st.info("🔄 Page will update automatically...")

    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {str(e)}")
        st.error(f"❌ Error cancelling order: {str(e)}")


def _handle_request_support(user_name, user_role, order_id, clean_room,
                            send_to_firebase, update_firebase_node):
    """Open a parallel support sub-channel inside chats/{order_id} and tag admin staff."""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        support_node = f"chats/{order_id}/support_request"
        support_data = {
            "active": True,
            "requested_by": user_name,
            "requested_role": user_role,
            "requested_at": now_str,
            "status": "awaiting_admin",
        }

        if update_firebase_node:
            success = update_firebase_node(support_node, support_data)
            if not success:
                st.error("❌ Failed to open support channel. Please try again.")
                return
        else:
            st.warning("⚠️ Database update service is currently unavailable.")
            return

        support_chat_node = f"chats/{order_id}/support_messages"
        try:
            send_to_firebase(support_chat_node, {
                "role": "System",
                "sender": "🚨 Support System",
                "message": f"Support channel opened for Order {order_id} by {user_name}. Admin team will receive immediate notification.",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post initial support message: {str(msg_err)}")

        try:
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": "System",
                "sender": "🚨 Support System",
                "message": f"🚨 Support has been requested for Order {order_id} — Admin team is being notified.",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post support notification to chat: {str(msg_err)}")

        st.success("Support channel opened successfully! Admin team has been notified.")
        st.info("🔄 Support banner will appear at the top for all participants.")

    except Exception as e:
        logger.error(f"Error requesting support for order {order_id}: {str(e)}")
        st.error(f"❌ Error requesting support: {str(e)}")


def _render_support_banner(order_id, fetch_firebase_raw):
    """Show a live support banner if a support request is active for this order."""
    if not fetch_firebase_raw:
        return
    try:
        support_data = fetch_firebase_raw(f"chats/{order_id}/support_request")
        if not support_data or not isinstance(support_data, dict):
            return

        is_active = support_data.get("active", False)
        requester = support_data.get("requested_by", "")
        requested_at = support_data.get("requested_at", "")

        if is_active:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #ff4444, #cc0000); color: white;
                        padding: 12px 16px; border-radius: 10px; margin-bottom: 12px;'>
                <strong>🚨 Support Required</strong> — Admin team has been called for Order <code style='color: #ffcccc;'>{html.escape(str(order_id))}</code>
                <br><span style='font-size: 0.85em; opacity: 0.9;'>
                    Requested by: {html.escape(str(requester))} • {html.escape(str(requested_at))}
                </span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Error checking support status for order {order_id}: {str(e)}")


# ==============================================================================
# 🕵️‍♂️ 4. TRACKING VIEW (شاشة تتبع الطلب للعميل)
# ==============================================================================

def render_customer_tracking(fetch_from_firebase, get_live_distance_for_order, format_distance_display, **kwargs):
    """Render customer order tracking view with flexible **kwargs."""
    st.subheader("🕵️‍♂️ Track Your Current Order:")
    orders = fetch_from_firebase("orders")
    my_order = None
    if orders and st.session_state.get("my_active_order_id"):
        my_order = next((o for o in orders if o.get("order_id") == st.session_state["my_active_order_id"]), None)

    if my_order:
        st.info(f"📦 Order ID: {my_order.get('order_id')} | Status: **{my_order.get('status')}**")
        if my_order.get("status") == "Driver En Route":
            st.success(f"⚡ Alert: Driver ({my_order.get('driver')}) has accepted your order and is on the way!")
            distance = get_live_distance_for_order(my_order)
            distance_text = format_distance_display(distance)
            st.metric(label="Live Distance to Driver", value=distance_text)
        
        payment_method = my_order.get("payment_method", "Unknown")
        st.markdown(f"**💳 نوع الدفع:** {payment_method}")
        st.metric(label="Fare Amount", value=f"EGP {my_order.get('price')}")
    else:
        st.warning("📭 No active order to track. Create a parcel or taxi order to get started.")
