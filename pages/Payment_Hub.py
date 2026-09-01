import streamlit as st
import streamlit.components.v1 as components
from paymob import initiate_wallet_topup

st.set_page_config(
    page_title="منصة مُنجز - بوابة الدفع الموحدة", layout="wide"
)


def render_payment_hub(purpose="topup", default_amount=100):
    st.markdown("### 💳 مركز الدفع والتغذية المالية الموحد")

    # جلب بيانات المستخدم الحالي تلقائياً من الجلسة
    user_data = st.session_state.get(
        "user_data",
        {
            "name": "ahmed mostafa mohammed",
            "phone": "+201000000000",
            "email": "user@monjez.online",
            "role": "driver",
        },
    )

    user_name = user_data.get("name", "مستخدم منجز")
    user_phone = user_data.get("phone", "+201000000000")
    user_email = user_data.get("email", "user@monjez.online")

    st.info(
        f"👤 **المستخدم:** {user_name} | 📱 **الهاتف:** {user_phone} | 🎭 **الدور:** {user_data.get('role')}"
    )

    # تحديد غرض العملية المالية
    purposes_map = {
        "topup": "📱 شحن رصيد المحفظة الشخصية",
        "debt": "📉 تسديد مديونية حساب السائق / المندوب",
        "ai_sub": "🤖 تجديد اشتراك كابلوت الذكاء الاصطناعي (مُنجز AI)",
        "order": "📦 تسديد فاتورة رحلة / شحنة ميدانية",
    }

    selected_purpose_key = st.selectbox(
        "اختر غرض العملية المالية:",
        options=list(purposes_map.keys()),
        format_func=lambda x: purposes_map[x],
        index=list(purposes_map.keys()).index(purpose)
        if purpose in purposes_map
        else 0,
    )

    amount = st.number_input(
        "أدخل المبلغ المطلوب سداده (بالجنيه المصري):",
        min_value=10,
        value=int(default_amount),
        step=10,
    )

    payment_method = st.radio(
        "اختر طريقة الدفع المفضلة:",
        ["💳 بطاقة أئتمان / ميزة", "📱 محفظة إلكترونية (فودافون كاش)"],
        horizontal=True,
    )
    method_code = "wallet" if "محفظة" in payment_method else "card"

    if st.button(
        "🚀 الانتقال لبوابة الدفع الإلكتروني الآمنة",
        use_container_width=True,
    ):
        name_parts = user_name.split()
        driver_info = {
            "first_name": name_parts[0] if name_parts else "User",
            "last_name": name_parts[-1] if len(name_parts) > 1 else "Monjez",
            "phone_number": user_phone,
            "email": user_email,
        }

        with st.spinner("جاري التواصل مع بوابة Paymob..."):
            res = initiate_wallet_topup(
                driver_username=user_name,
                amount_egp=amount,
                driver_info=driver_info,
                payment_method=method_code,
            )

            if res and res.get("checkout_url"):
                st.session_state["payment_hub_url"] = res["checkout_url"]
                st.session_state["payment_hub_order_id"] = res["order_id"]
                st.success(
                    f"✅ تم فتح المعاملة المالية رقم #{res['order_id']} بنجاح!"
                )
            else:
                st.error(
                    "❌ تعذر الاتصال ببوابة Paymob. يرجى مراجعة ضبط Secrets في Streamlit."
                )

    # عرض نافذة Iframe الخاصة بالدفع فور توفر الرابط
    if "payment_hub_url" in st.session_state:
        st.markdown("---")
        st.markdown(
            f"##### 🔒 نافذة الدفع الآمنة (معاملة #{st.session_state.get('payment_hub_order_id')})"
        )
        components.html(
            f"""
            <iframe 
                src="{st.session_state['payment_hub_url']}" 
                width="100%" 
                height="650" 
                frameborder="0" 
                allow="geolocation">
            </iframe>
            """,
            height=670,
        )


if __name__ == "__main__":
    render_payment_hub()
