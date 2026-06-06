import html as html_mod
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore

st.set_page_config(page_title="منصة مُنجز - بوابة العميل", layout="wide", initial_sidebar_state="expanded")

# --- الاتصال الآمن بالفايربيز ---
db = init_firestore()
if db is None:
    st.error("❌ اتصال السيرفر معطل")

# --- بروفايل العميل الجانبي (DiDi Style) ---
st.sidebar.markdown("""
<div style='text-align: center; background-color: #F3F4F6; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
    <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' style='width: 75px; border-radius: 50%; border: 2px solid #1E3A8A;'>
    <h3 style='margin: 10px 0 2px 0; color: #1E3A8A;'>AHMED mostafa</h3>
    <a href='#' style='text-decoration: none; color: #6B7280; font-size: 13px;'>تعديل المعلومات الشخصية ✏️</a>
</div>
""", unsafe_allow_html=True)

# قائمة التحكم المتطابقة مع الصورة
client_menu = st.sidebar.radio("📌 انتقل إلى:", [
    "🚖 اطلب مشوار / توصيل الآن", 
    "📜 مشاويري السابقة", 
    "💳 محفظة الدفع الإلكتروني", 
    "🛡️ مركز السلامة والطوارئ",
    "⚙️ إعدادات التطبيق"
])

if client_menu == "🚖 اطلب مشوار / توصيل الآن":
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🛒 طلب خدمة توصيل ومزايدة حية</h2>", unsafe_allow_html=True)
    
    # واجهة إدخال الطلب المحدثة
    with st.form("new_order_form", clear_on_submit=True):
        c_name = st.text_input("👤 اسم العميل الافتراضي", value="أحمد مصطفى")
        o_details = st.text_area("📝 ما الذي تريد توصيله؟ (اكتب تفاصيل الوجهة والشحنة بدقة)", placeholder="مثال: مطلوب استلام طرد من ماكدونالدز فرع الزمالك وتوصيله إلى المهندسين...")
        s_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30, step=5)
        c_phone = st.text_input("📱 رقم هاتف التواصل الحركي", value="+20 1000000000")
        
        submit_btn = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض السائقين")
        
        if submit_btn and db:
            if o_details.strip() == "":
                st.warning("⚠️ يرجى كتابة تفاصيل الشحنة أولاً قبل النشر!")
            else:
                db.collection("orders").add({
                    "client_name": c_name,
                    "order_details": o_details,
                    "suggested_price": s_price,
                    "phone": c_phone,
                    "status": "processing",
                    "driver_assigned": "",
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("🎯 عظيم يا هندسة! تم قيد ونشر طلبك في الميدان بنجاح.")

    # رادار تتبع الحالات النشطة (يمنع التكرار نهائياً)
    st.markdown("---")
    st.markdown("<h3 style='color: #10B981; text-align: right;'>📋 مراقبة وتتبع طلباتك الحالية</h3>", unsafe_allow_html=True)
    
    if db:
        orders_stream = db.collection("orders").where("client_name", "==", "أحمد مصطفى").stream()
        active_found = False
        
        for doc in orders_stream:
            data = doc.to_dict()
            status = data.get("status")
            
            # نعرض فقط الطلبات المفتوحة والنشطة
            if status != "⭐ تم الإغلاق والتقييم بالكامل":
                active_found = True
                driver = data.get("driver_assigned", "جاري البحث عن كابتن...")
                price = data.get("suggested_price", 30)
                
                st.markdown(f"""
                <div style='background-color: #EFF6FF; padding: 15px; border-radius: 8px; border-right: 5px solid #3B82F6; margin-bottom: 10px; text-align: right;'>
                    <b style='color: #1E3A8A; font-size: 16px;'>✔️ تم قبول طلبك وبدأ التنفيذ الحقيقي!</b><br>
                    <span style='color: #333;'>👤 الكابتن المسؤول: {html_mod.escape(str(driver)) if driver else 'جاري الاستلام'}</span><br>
                    <span style='color: #333;'>💰 السعر المتفق عليه: {html_mod.escape(str(price))} جنيه</span><br>
                    <span style='color: #DC2626;'>🚨 حالة التحرك الحية الآن: 🚖 {html_mod.escape(str(status))}</span>
                </div>
                """, unsafe_allow_html=True)
                
        if not active_found:
            st.info("💡 لا توجد لديك طلبات نشطة في الوقت الحالي. رحلاتك القادمة ستظهر هنا فورا.")

elif client_menu == "📜 مشاويري السابقة":
    st.subheader("📜 دفتر سجل رحلاتك")
    st.caption("يتيح لك مراجعة الأماكن والأسعار السابقة لرحلاتك مع منجز.")

elif client_menu == "💳 محفظة الدفع الإلكتروني":
    st.subheader("💳 رصيد حسابك الذكي")
    st.metric("الرصيد المتاح للعميل", "0.00 ج.م")

elif client_menu == "🛡️ مركز السلامة والطوارئ":
    st.subheader("🛡️ نظام الأمان والسلامة")
    st.error("🚨 زر الاستغاثة (SOS): بمجرد الضغط عليه، يتم إرسال موقعك الجغرافي الحي فوراً لغرفة عمليات وموظفي منجز للتدخل الصارم لحمايتك.")

elif client_menu == "⚙️ إعدادات التطبيق":
    st.subheader("⚙️ تفضيلات المستخدم والخصومات")
