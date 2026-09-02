import html as html_mod
import requests
import time
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore

# Defensive import of payment hub
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub
    except Exception:
        render_payment_hub = None

# --- الاتصال بقاعدة بيانات فايربيز ---
try:
    db = init_firestore()
except Exception:
    db = None
    try:
        st.sidebar.warning("⚠️ Firebase غير متصل. بعض الميزات ستكون معطلة.")
    except Exception:
        pass

# ---------------------------------------------------------
# 1️⃣ دالة بوابة الطرود والمرسول
# ---------------------------------------------------------
def render_parcels_page(user_name="أحمد مصطفى", send_to_firebase=None, send_system_email=None, *args, **kwargs):
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>📦 بوابة توصيل الطرود والمرسول</h2>", unsafe_allow_html=True)
    
    # Live Order Tracker (integrated with order_lifecycles)
    st.markdown("### 🔴 Live Order Tracker")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("تحديث اللحظة 🔄", key="client_live_refresh"):
            st.rerun()
    with col1:
        if db:
            try:
                user_name_val = user_name
                orders_q = db.collection("order_lifecycles").where("customer_name", "==", user_name_val).stream()
            except Exception as e:
                st.error(f"خطأ في جلب حالة الطلبات: {e}")
                orders_q = []

            shown = False
            for doc in orders_q:
                try:
                    shown = True
                    o = doc.to_dict() or {}
                    o_id = doc.id
                    status = o.get("status", "pending")
                    status_color = "#F59E0B" if status == "pending" else ("#10B981" if status in ["picked_up", "in_transit"] else ("#2563EB" if status == "bid_accepted" else "#6B7280"))
                    st.markdown(f"<div style='padding:12px; border-radius:8px; background:{status_color}; color:white; text-align:right;'><b>حالة الطلب: {status.upper()}</b></div>", unsafe_allow_html=True)

                    bids = o.get("bids", []) or []
                    if not bids:
                        st.info("لا توجد عروض بعد. يرجى الانتظار حتى يقدم المندوبون عروضهم.")
                    else:
                        st.markdown("#### العروض المقدمة")
                        for idx, b in enumerate(bids):
                            driver = b.get("driver_name", b.get("by", "غير معروف"))
                            amount = b.get("bid_amount", b.get("bid", "-"))
                            st.write(f"- {driver}: {amount} ج.م")
                            if st.button("قبول العرض", key=f"accept_bid_{o_id}_{idx}"):
                                try:
                                    db.collection("order_lifecycles").document(o_id).update({
                                        "accepted_bid_index": idx,
                                        "assigned_driver": driver,
                                        "final_price": amount,
                                        "status": "bid_accepted",
                                        "bid_accepted_at": firestore.SERVER_TIMESTAMP,
                                    })
                                    st.success("✅ تم قبول العرض وسيتم إشعار السائق المختار.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"فشل قبول العرض: {e}")
                except Exception:
                    continue
            if not shown:
                st.info("لا توجد طلبيات مرتبطة باسمك حالياً.")

    st.markdown("---")
    
    # Form for creating parcel order
    with st.form("parcels_form", clear_on_submit=True):
        c_name = st.text_input("👤 اسم العميل", value=user_name if isinstance(user_name, str) else "أحمد مصطفى", key="parcels_name")
        o_details = st.text_area("📝 ما الذي تريد توصيله؟ (اكتب تفاصيل الوجهة والشحنة بدقة)", placeholder="مثال: مطلوب استلام طرد من...", key="parcels_details")
        s_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30, step=5, key="parcels_price")
        c_phone = st.text_input("📱 رقم هاتف التواصل", value="+20 1000000000", key="parcels_phone")

        submit_btn = st.form_submit_button("🚀 نشر طلب الطرد", key="parcels_submit")
        
    if submit_btn:
        if not o_details or not o_details.strip():
            st.warning("⚠️ يرجى كتابة تفاصيل الشحنة أولاً قبل النشر!")
        else:
            payload = {
                "customer_name": c_name,
                "order_type": "parcel",
                "order_details": o_details,
                "customer_budget": s_price,
                "phone": c_phone,
                "status": "pending",
                "assigned_driver": "",
                "created_at": firestore.SERVER_TIMESTAMP,
            }
            try:
                if callable(send_to_firebase):
                    send_to_firebase(f"order_lifecycles/{int(time.time())}", payload)
                    st.success("🎯 تم قيد ونشر طلب الطرد بنجاح!")
                else:
                    if not db:
                        st.error("⚠️ Firebase غير متصل — لا يمكن حفظ الطلب الآن.")
                    else:
                        db.collection("order_lifecycles").add(payload)
                        st.success("🎯 تم قيد ونشر طلب الطرد بنجاح!")
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء حفظ الطلب: {e}")

# ---------------------------------------------------------
# 2️⃣ دالة طلب تاكسي / توصيل أفراد
# ---------------------------------------------------------
def render_taxi_page(user_name="أحمد مصطفى", send_to_firebase=None, send_system_email=None, *args, **kwargs):
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🚖 طلب تاكسي وتوصيل أفراد</h2>", unsafe_allow_html=True)
    
    st.markdown("### 🔴 Live Order Tracker")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("تحديث اللحظة 🔄", key="client_taxi_refresh"):
            st.rerun()
    with col1:
        if db:
            try:
                orders_q = db.collection("order_lifecycles").where("customer_name", "==", user_name).stream()
            except Exception as e:
                st.error(f"خطأ في جلب حالة الطلبات: {e}")
                orders_q = []

            shown = False
            for doc in orders_q:
                try:
                    shown = True
                    o = doc.to_dict() or {}
                    o_id = doc.id
                    status = o.get("status", "pending")
                    st.markdown(f"<div style='padding:12px; border-radius:8px; background:#F3F4F6; text-align:right;'><b>حالة الطلب: {status.upper()}</b></div>", unsafe_allow_html=True)

                    bids = o.get("bids", []) or []
                    if bids:
                        st.markdown("#### العروض المقدمة")
                        for idx, b in enumerate(bids):
                            driver = b.get("driver_name", b.get("by", "غير معروف"))
                            amount = b.get("bid_amount", b.get("bid", "-"))
                            st.write(f"- {driver}: {amount} ج.م")
                            if st.button("قبول العرض", key=f"accept_taxi_{o_id}_{idx}"):
                                try:
                                    db.collection("order_lifecycles").document(o_id).update({
                                        "accepted_bid_index": idx,
                                        "assigned_driver": driver,
                                        "final_price": amount,
                                        "status": "bid_accepted",
                                        "bid_accepted_at": firestore.SERVER_TIMESTAMP,
                                    })
                                    st.success("✅ تم قبول العرض وسيتم إشعار السائق المختار.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"فشل قبول العرض: {e}")
                except Exception:
                    continue
            if not shown:
                st.info("لا توجد طلبيات مرتبطة باسمك حالياً.")

    with st.form("taxi_form", clear_on_submit=True):
        c_name = st.text_input("👤 اسم العميل", value=user_name if isinstance(user_name, str) else "أحمد مصطفى", key="taxi_name")
        o_details = st.text_area("📝 تفاصيل المشوار والوجهة", placeholder="مثال: التوصيل من شارع التحرير إلى الدقي...", key="taxi_details")
        s_price = st.number_input("💰 الميزانية المقترحة للرحلة (جنيه)", min_value=10, value=50, step=5, key="taxi_price")
        c_phone = st.text_input("📱 رقم هاتف التواصل", value="+20 1000000000", key="taxi_phone")

        submit_taxi_btn = st.form_submit_button("🚀 طلب التاكسي الآن", key="taxi_submit")
        
    if submit_taxi_btn:
        if not o_details or not o_details.strip():
            st.warning("⚠️ يرجى تحديد تفاصيل المشوار والوجهة أولاً!")
        else:
            payload = {
                "customer_name": c_name,
                "order_type": "taxi",
                "order_details": o_details,
                "customer_budget": s_price,
                "phone": c_phone,
                "status": "pending",
                "assigned_driver": "",
                "created_at": firestore.SERVER_TIMESTAMP,
            }
            try:
                if callable(send_to_firebase):
                    send_to_firebase(f"order_lifecycles/{int(time.time())}", payload)
                    st.success("🎯 تم نشر طلب الرحلة وبدأ البحث عن سائق!")
                else:
                    if not db:
                        st.error("⚠️ Firebase غير متصل — لا يمكن حفظ الطلب الآن.")
                    else:
                        db.collection("order_lifecycles").add(payload)
                        st.success("🎯 تم نشر طلب الرحلة وبدأ البحث عن سائق!")
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء حفظ الطلب: {e}")

# ---------------------------------------------------------
# 3️⃣ دالة شات مُنجز الخاص
# ---------------------------------------------------------
def render_chat_page(user_name="أحمد مصطفى", user_role="client", send_to_firebase=None, *args, **kwargs):
    st.subheader("💬 شات مُنجز المباشر")
    st.info(f"مرحباً بك {user_name} ({user_role}) في غرفة المحادثة المباشرة.")
    
    chat_msg = st.text_input("أدخل رسالتك:", key="client_chat_msg")
    if st.button("إرسال", key="client_send_msg"):
        if chat_msg and chat_msg.strip():
            payload = {
                "sender": user_name,
                "role": user_role,
                "message": chat_msg,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            try:
                if callable(send_to_firebase):
                    send_to_firebase("chats", payload)
                    st.success("تم إرسال الرسالة!")
                else:
                    if not db:
                        st.error("⚠️ Firebase غير متصل — لا يمكن إرسال الرسالة الآن.")
                    else:
                        db.collection("chats").add(payload)
                        st.success("تم إرسال الرسالة!")
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء إرسال الرسالة: {e}")

# ---------------------------------------------------------
# 4️⃣ دالة المحفظة الإلكترونية
# ---------------------------------------------------------
def render_wallet_page(user_name="أحمد مصطفى", *args, **kwargs):
    st.subheader("💳 محفظة الدفع الذكية")
    
    current_balance = 0.0
    if db:
        try:
            users_q = db.collection("users").where("full_name", "==", user_name).limit(1).get()
            if users_q and len(users_q) > 0:
                current_balance = float(users_q[0].to_dict().get("wallet_balance", 0.0))
        except Exception:
            current_balance = 0.0
    else:
        st.info("⚠️ خاصية المحفظة تعمل في وضع محدود لأن خدمة البيانات غير متاحة حالياً.")
            
    col_bal, col_btn = st.columns([3, 1])
    with col_bal:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px;'>
            <p style='margin: 0; font-size: 14px;'>رصيد الحساب الحالي</p>
            <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: bold;'>{current_balance:.2f} ج.م</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_btn:
        with st.expander("➕ إضافة", expanded=False):
            topup_amount = st.number_input("المبلغ المراد إضافته", min_value=10, value=100, key="wallet_topup_amount")
            if st.button("دفع", type="primary", key="wallet_topup_btn"):
                if render_payment_hub:
                    try:
                        render_payment_hub(purpose="topup", default_amount=int(topup_amount))
                    except Exception:
                        st.error("❌ تعذر فتح بوابة الدفع حاليًا.")
                else:
                    st.info("⚠️ بوابة الدفع غير متاحة — تأكد من توافر صفحة Payment_Hub.") 

# ---------------------------------------------------------
# نقطة الدخول الرئيسية (Main Entrypoint)
# ---------------------------------------------------------
def main():
    st.title("منصة مُنجز - واجهة العميل")
    menu = ["بوابة الطرود", "طلب تاكسي", "الشات", "المحفظة"]
    choice = st.sidebar.selectbox("القائمة", menu)

    user_name = st.session_state.get("user_data", {}).get("name", "أحمد مصطفى")

    if choice == "بوابة الطرود":
        render_parcels_page(user_name=user_name)
    elif choice == "طلب تاكسي":
        render_taxi_page(user_name=user_name)
    elif choice == "الشات":
        render_chat_page(user_name=user_name)
    elif choice == "المحفظة":
        render_wallet_page(user_name=user_name)

# تشغيل آمن لتفادي الشاشة البيضاء وتتبع الأخطاء بالسجلات
try:
    main()
except Exception as e:
    try:
        st.error("حدث خطأ غير متوقع في واجهة العميل. سيتم تسجيل التفاصيل في السجلات.")
    except Exception:
        pass
    import logging
    logging.exception("Unhandled error in pages/1_Client.py: %s", e)
