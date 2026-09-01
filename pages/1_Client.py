import html as html_mod
import time
import os
import requests
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore

# استيراد بوابة الدفع الموحدة
try:
    from pages.Payment_Hub import render_payment_hub
except ImportError:
    from Payment_Hub import render_payment_hub

# --- الاتصال بالفايربيز ---
db = init_firestore()


# ---------------------------------------------------------
# 1️⃣ دالة بوابة الطرود والمرسول
# ---------------------------------------------------------
def render_parcels_page(
    user_name="أحمد مصطفى",
    send_to_firebase=None,
    send_system_email=None,
    *args,
    **kwargs,
):
    st.markdown(
        "<h2 style='color: #1E3A8A; text-align: right;'>📦 بوابة توصيل الطرود والمرسول</h2>",
        unsafe_allow_html=True,
    )

    with st.form("parcels_form", clear_on_submit=True):
        c_name = st.text_input(
            "👤 اسم العميل",
            value=user_name if isinstance(user_name, str) else "أحمد مصطفى",
        )
        o_details = st.text_area(
            "📝 ما الذي تريد توصيله؟ (اكتب تفاصيل الوجهة والشحنة بدقة)",
            placeholder="مثال: مطلوب استلام طرد من...",
        )
        s_price = st.number_input(
            "💰 ميزانيتك المقترحة للطلب (جنيه)",
            min_value=10,
            value=30,
            step=5,
        )
        c_phone = st.text_input("📱 رقم هاتف التواصل", value="+20 1000000000")

        submit_btn = st.form_submit_button("🚀 نشر طلب الطرد")

        if submit_btn:
            if not o_details.strip():
                st.warning("⚠️ يرجى كتابة تفاصيل الشحنة أولاً قبل النشر!")
            else:
                payload = {
                    "client_name": c_name,
                    "order_details": o_details,
                    "suggested_price": s_price,
                    "phone": c_phone,
                    "status": "processing",
                    "driver_assigned": "",
                    "timestamp": firestore.SERVER_TIMESTAMP,
                }
                try:
                    if callable(send_to_firebase):
                        send_to_firebase("deliveries", payload)
                    elif db:
                        db.collection("deliveries").add(payload)
                    st.success("🎯 تم قيد ونشر طلب الطرد بنجاح!")
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء حفظ الطلب: {e}")


# ---------------------------------------------------------
# 2️⃣ دالة طلب تاكسي / توصيل أفراد
# ---------------------------------------------------------
def render_taxi_page(
    user_name="أحمد مصطفى",
    send_to_firebase=None,
    send_system_email=None,
    *args,
    **kwargs,
):
    st.markdown(
        "<h2 style='color: #1E3A8A; text-align: right;'>🚖 طلب تاكسي وتوصيل أفراد</h2>",
        unsafe_allow_html=True,
    )

    with st.form("taxi_form", clear_on_submit=True):
        c_name = st.text_input(
            "👤 اسم العميل",
            value=user_name if isinstance(user_name, str) else "أحمد مصطفى",
        )
        o_details = st.text_area(
            "📝 تفاصيل المشوار والوجهة",
            placeholder="مثال: التوصيل من شارع التحرير إلى الدقي...",
        )
        s_price = st.number_input(
            "💰 الميزانية المقترحة للرحلة (جنيه)",
            min_value=10,
            value=50,
            step=5,
        )
        c_phone = st.text_input("📱 رقم هاتف التواصل", value="+20 1000000000")

        submit_btn = st.form_submit_button("🚀 طلب التاكسي الآن")

        if submit_btn:
            if not o_details.strip():
                st.warning("⚠️ يرجى تحديد تفاصيل المشوار والوجهة أولاً!")
            else:
                payload = {
                    "client_name": c_name,
                    "order_details": o_details,
                    "suggested_price": s_price,
                    "phone": c_phone,
                    "status": "processing",
                    "driver_assigned": "",
                    "timestamp": firestore.SERVER_TIMESTAMP,
                }
                try:
                    if callable(send_to_firebase):
                        send_to_firebase("rides", payload)
                    elif db:
                        db.collection("rides").add(payload)
                    st.success("🎯 تم نشر طلب الرحلة وبدأ البحث عن سائق!")
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء حفظ الطلب: {e}")


# ---------------------------------------------------------
# 3️⃣ دالة شات مُنجز الخاص
# ---------------------------------------------------------
def render_chat_page(
    user_name="أحمد مصطفى",
    user_role="client",
    send_to_firebase=None,
    *args,
    **kwargs,
):
    st.subheader("💬 شات مُنجز المباشر")
    st.info(f"مرحباً بك {user_name} ({user_role}) في غرفة المحادثة المباشرة.")

    chat_msg = st.text_input("أدخل رسالتك:")
    if st.button("إرسال"):
        if chat_msg.strip():
            payload = {
                "sender": user_name,
                "role": user_role,
                "message": chat_msg,
                "timestamp": firestore.SERVER_TIMESTAMP,
            }
            try:
                if callable(send_to_firebase):
                    send_to_firebase("chats", payload)
                elif db:
                    db.collection("chats").add(payload)
                st.success("تم إرسال الرسالة!")
            except Exception as e:
                st.error(f"❌ خطأ أثناء إرسال الرسالة: {e}")


# ---------------------------------------------------------
# 4️⃣ دالة المحفظة الإلكترونية + بوابة Paymob
# ---------------------------------------------------------
def render_wallet_page(user_name="أحمد مصطفى", *args, **kwargs):
    st.subheader("💳 محفظة الدفع الذكية")

    current_balance = 0.0
    if db:
        try:
            users_q = (
                db.collection("users")
                .where("full_name", "==", user_name)
                .limit(1)
                .get()
            )
            if users_q and len(users_q) > 0:
                current_balance = float(
                    users_q[0].to_dict().get("wallet_balance", 0.0)
                )
        except Exception:
            current_balance = 0.0

    col_bal, col_btn = st.columns([3, 1])
    with col_bal:
        st.markdown(
            f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px;'>
            <p style='margin: 0; font-size: 14px;'>رصيد الحساب الحالي</p>
            <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: bold;'>{current_balance:.2f} ج.م</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_btn:
        with st.popover("➕ إضافة رصيد", use_container_width=True):
            topup_amount = st.number_input(
                "المبلغ المراد إضافته", min_value=10, value=100
            )
            if st.button("بدء الشحن عبر Paymob", type="primary", use_container_width=True):
                st.session_state["show_paymob_hub"] = True
                st.session_state["paymob_topup_amt"] = topup_amount

    # عرض بوابة الدفع عند الضغط على زر الشحن
    if st.session_state.get("show_paymob_hub"):
        st.markdown("---")
        render_payment_hub(
            purpose="topup",
            default_amount=st.session_state.get("paymob_topup_amt", 100),
        )


# ---------------------------------------------------------
# 5️⃣ نقطة التشغيل الرئيسية واجهة التبويبات (تمنع الشاشة البيضاء)
# ---------------------------------------------------------
def main():
    user_name = st.session_state.get("user_name", "أحمد مصطفى")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📦 شحن طرد", "🚖 طلب تاكسي", "💳 المحفظة", "💬 المحادثة"]
    )

    with tab1:
        render_parcels_page(user_name=user_name)
    with tab2:
        render_taxi_page(user_name=user_name)
    with tab3:
        render_wallet_page(user_name=user_name)
    with tab4:
        render_chat_page(user_name=user_name)


# استدعاء دالة التشغيل مباشرة عند فتح الصفحة
main()
