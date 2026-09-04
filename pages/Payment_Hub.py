import streamlit as st
import streamlit.components.v1 as components
import requests

def _get_secret(path, default=None):
    """جلب الأسرار بشكل آمن من st.secrets سواء في الجذر أو داخل قسم paymob."""
    try:
        # 1. البحث المباشر في المسار المطلوب
        parts = path.split('.')
        cur = st.secrets
        found = True
        for p in parts:
            if not isinstance(cur, dict) or p not in cur:
                found = False
                break
            cur = cur[p]
        if found and cur:
            return cur
            
        # 2. البحث الاحتياطي داخل قسم paymob
        if path.startswith("PAYMOB_") and "paymob" in st.secrets:
            if path in st.secrets["paymob"]:
                return st.secrets["paymob"][path]
                
        return default
    except Exception:
        return default

def test_paymob_connection(api_key):
    """دالة مستقلة لاختبار صحة مفتاح Paymob API مباشرة وجلب التوكن."""
    url = "https://accept.paymob.com/api/auth/tokens"
    try:
        response = requests.post(url, json={"api_key": api_key}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data.get("token")
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

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

    # فحص المفتاح وقراءته تلقائياً من أي مكان تم تخزينه فيه
    paymob_key = _get_secret("PAYMOB_API_KEY") or _get_secret("paymob.PAYMOB_API_KEY")

    # صندوق اختبار حالة المفتاح للمطور
    with st.expander("🛠️ فحص حالة اتصال واختبار مفتاح Paymob"):
        if paymob_key:
            st.success("✅ تم العثور على مفتاح API في الإعدادات.")
            if st.button("اختبار الاتصال الفعلي بـ Paymob"):
                with st.spinner("جاري فحص المفتاح مع سيرفرات Paymob..."):
                    success, result = test_paymob_connection(paymob_key)
                    if success:
                        st.success("🎉 المفتاح صحيح 100% وتم الاتصال بنجاح!")
                    else:
                        st.error(f"❌ فشل الاتصال: {result}")
        else:
            st.error("⚠️ المفتاح غير موجود نهائياً في Secrets.")

    if not paymob_key:
        st.warning("⚠️ إعدادات Paymob غير مكتملة في Streamlit. الرجاء إضافة PAYMOB_API_KEY داخل Secrets.")
        return

    # تحديد غرض العملية المالية
    purposes_map = {
        "topup": "📱 شحن رصيد المحفظة الشخصية",
        "debt": "📉 تسديد مديونية حساب السائق / المندوب",
        "ai_sub": "🤖 تجديد اشتراك الذكاء الاصطناعي (مُنجز AI)",
        "order": "📦 تسديد فاتورة رحلة / شحنة ميدانية",
    }

    selected_purpose_key = st.selectbox(
        "اختر غرض العملية المالية:",
        options=list(purposes_map.keys()),
        format_func=lambda x: purposes_map[x],
        index=list(purposes_map.keys()).index(purpose) if purpose in purposes_map else 0,
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

    if st.button("🚀 الانتقال لبوابة الدفع الإلكتروني الآمنة", use_container_width=True):
        with st.spinner("جاري إنشاء جلسة الدفع..."):
            success, token_or_err = test_paymob_connection(paymob_key)
            if not success:
                st.error(f"❌ خطأ في مصادقة المفتاح مع Paymob: {token_or_err}")
                return
            
            # محاكاة رابط ناجح للاختبار الفوري للشاشة
            iframe_id = _get_secret("PAYMOB_IFRAME_ID") or "1051892"
            test_checkout_url = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={token_or_err}"
            
            st.session_state["payment_hub_url"] = test_checkout_url
            st.session_state["payment_hub_order_id"] = "998877"
            st.success("✅ تم تجهيز رابط الدفع بنجاح!")

    # عرض نافذة Iframe الخاصة بالدفع فور توفر الرابط
    if "payment_hub_url" in st.session_state:
        st.markdown("---")
        st.markdown(f"##### 🔒 نافذة الدفع الآمنة")
        try:
            components.html(
                f"""
                <iframe src="{st.session_state['payment_hub_url']}" width="100%" height="650" frameborder="0" allow="geolocation"></iframe>
                """,
                height=670,
            )
        except Exception:
            st.error("❌ تعذر عرض نافذة الدفع الآمنة داخل التطبيق.")

if __name__ == "__main__":
    render_payment_hub()
