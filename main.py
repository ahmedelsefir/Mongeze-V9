import streamlit as st

# 1. إعدادات الصفحة الأساسية للمنصة
st.set_page_config(
    page_title="منصة مُنجز الذكية",
    page_icon="🚀",
    layout="wide"
)

# 2. تصميم واجهة العنوان الرئيسية والألوان الاحترافية
st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🚀 مرحباً بكم في منصة مُنجز</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555555;'>نظام الإدارة والخدمات اللوجستية المتكامل لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>اختر القسم الذي تود الدخول إليه:</h3>", unsafe_allow_html=True)
st.write("\n")

# 3. أزرار الانتقال القياسية (الآن السيرفر سيتعرف عليها تلقائياً فوراً)
if st.button("🛒 دخول بوابة العميل", use_container_width=True):
    st.switch_page("pages/1_Client.py")

st.write("\n")

if st.button("🚖 دخول بوابة السائق", use_container_width=True):
    st.switch_page("pages/2_Driver.py")

st.write("\n")

if st.button("📊 دخول بوابة المسؤول", use_container_width=True):
    st.switch_page("pages/3_Admin.py")

# 4. تذييل الصفحة
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 0.9rem;'>تم التصميم بمنتهى الدقة بواسطة فريق مُنجز التقني</p>", unsafe_allow_html=True)
# كود تجريبي لاختبار الإرسال (حطه في آخر الملف الرئيسي للتجربة)
st.write("---")
st.subheader("🧪 مركز اختبار فواتير مُنجز")

# خانة يكتب فيها بريدك الشخصي لتجربة الاستقبال
test_email = st.text_input("اكتب إيميلك الشخصي (الجيميل مثلاً) لتجربة الاستقبال:", "")

if st.button("🚀 إرسال فاتورة تجريبية لايف"):
    if test_email:
        # نص فاتورة تجريبي HTML منسق
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial; border: 1px solid #ccc; padding: 20px;">
            <h2 style="color: #FF5733;">منصة مُنجز - فاتورة تجريبية</h2>
            <p>مرحباً بك يا هندسة، هذا الإيميل يؤكد اتصال محرك زوهو بنجاح بالمنصة!</p>
            <hr>
            <p><b>حالة الاتصال:</b> ممتازة 100% ✅</p>
        </div>
        """
        with st.spinner("جاري إطلاق الفاتورة عبر سيرفر زوهو السيادي..."):
            # استدعاء الدالة اللي أنت كتبتها
            success = send_monjez_email(test_email, "تأكيد اتصال محرك منجز 🚀", sample_html)
            
            if success:
                st.success("✅ تم الإرسال بنجاح! افتح بريدك الشخصي الآن وتفقد صندوق الوارد أو الـ Spam.")
            else:
                st.error("❌ فشل الإرسال. تأكد من إيقاظ التطبيق وصحة الباسورد في الـ Secrets.")
    else:
        st.warning("رجاءً اكتب الإيميل أولاً.")
