import streamlit as st
from datetime import datetime
import json
from pathlib import Path

# إعدادات الصفحة
st.set_page_config(
    page_title="مركز المهندس - طلب خدمة",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# تنسيق CSS مخصص
st.markdown("""
<style>
    * {
        direction: rtl;
        text-align: right;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77e4;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .service-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .form-header {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
    
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-title">⚙️ مركز المهندس للتركيبات</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">نموذج طلب خدمة احترافي</div>', unsafe_allow_html=True)

# خط فاصل
st.markdown("---")

# معلومات الخدمات المتاحة
st.markdown("### 📋 الخدمات المتاحة")
col1, col2, col3, col4 = st.columns(4)

services_info = [
    ("📹", "تركيب كاميرات", "تركيب كاميرات مراقبة"),
    ("🔧", "صيانة كاميرات", "صيانة كاميرات"),
    ("📡", "تركيب دش", "تركيب طبق دش"),
    ("🛠️", "صيانة دش", "صيانة دش")
]

with col1:
    st.info(f"{services_info[0][0]} **{services_info[0][1]}**")
with col2:
    st.info(f"{services_info[1][0]} **{services_info[1][1]}**")
with col3:
    st.info(f"{services_info[2][0]} **{services_info[2][1]}**")
with col4:
    st.info(f"{services_info[3][0]} **{services_info[3][1]}**")

st.markdown("---")

# النموذج الرئيسي
st.markdown("### ✍️ نموذج الطلب")

with st.form("service_request", clear_on_submit=True):
    
    # الصف الأول
    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input(
            "👤 الأسم بالكامل",
            placeholder="أدخل اسمك الكامل",
            key="name"
        )
    with col2:
        phone_number = st.text_input(
            "📱 رقم الواتساب",
            placeholder="أدخل رقم الواتساب (مثال: 201012345678)",
            key="phone"
        )
    
    # الصف الثاني
    col1, col2 = st.columns(2)
    with col1:
        service_type = st.selectbox(
            "🔍 نوع الخدمة المطلوبة",
            [
                "تركيب كاميرات مراقبة 📹",
                "صيانة كاميرات 🔧",
                "تركيب طبق دش 📡",
                "صيانة دش 🛠️"
            ],
            key="service"
        )
    with col2:
        preferred_date = st.date_input(
            "📅 موعد المعاينة المفضل",
            key="date"
        )
    
    # العنوان
    address = st.text_area(
        "🏠 العنوان بالتفصيل",
        placeholder="أدخل العنوان كاملاً (المحافظة - المدينة - الشارع - الحي)",
        height=100,
        key="address"
    )
    
    # الملاحظات الإضافية
    notes = st.text_area(
        "📝 ملاحظات إضافية",
        placeholder="أي تفاصيل إضافية مهمة...",
        height=80,
        key="notes"
    )
    
    # زر الإرسال
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.form_submit_button(
            "✅ إرسال الطلب",
            use_container_width=True
        )

# معالجة الطلب
if submit_button:
    # التحقق من البيانات
    if not client_name or not client_name.strip():
        st.error("❌ برجاء إدخال الأسم بالكامل")
        st.stop()
    
    if not phone_number or not phone_number.strip():
        st.error("❌ برجاء إدخال رقم الواتساب")
        st.stop()
    
    # التحقق من صيغة رقم الهاتف
    phone_clean = phone_number.strip()
    if not phone_clean.isdigit() or len(phone_clean) < 10:
        st.error("❌ رقم الهاتف غير صحيح. يجب أن يكون رقماً بـ 10 أرقام على الأقل")
        st.stop()
    
    if not address or not address.strip():
        st.error("❌ برجاء إدخال العنوان بالتفصيل")
        st.stop()
    
    # إذا كانت جميع البيانات صحيحة
    request_data = {
        "name": client_name.strip(),
        "phone": phone_number.strip(),
        "service": service_type.split()[0],  # إزالة الإيموجي
        "address": address.strip(),
        "date": str(preferred_date),
        "notes": notes.strip(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # حفظ البيانات (يمكن تطويرها لـ Firebase لاحقاً)
    try:
        requests_file = Path("service_requests.json")
        requests_list = []
        
        if requests_file.exists():
            with open(requests_file, 'r', encoding='utf-8') as f:
                requests_list = json.load(f)
        
        requests_list.append(request_data)
        
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(requests_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"⚠️ تم استلام طلبك لكن حدثت مشكلة في الحفظ: {str(e)}")
    
    # رسالة النجاح
    st.success(f"✅ تم استلام طلبك بنجاح يا {client_name}!")
    st.info(f"📞 سنتواصل معك عبر واتساب على الرقم: {phone_number}")
    st.balloons()
    
    # عرض ملخص الطلب
    st.markdown("### 📄 ملخص طلبك:")
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.write(f"**👤 الأسم:** {client_name}")
        st.write(f"**📱 الواتساب:** {phone_number}")
        st.write(f"**🔍 الخدمة:** {service_type}")
    
    with summary_col2:
        st.write(f"**🏠 العنوان:** {address}")
        st.write(f"**📅 الموعد:** {preferred_date}")
        if notes:
            st.write(f"**📝 ملاحظات:** {notes}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p>⚙️ <b>مركز المهندس للتركيبات</b></p>
    <p>متخصصون في تركيب وصيانة كاميرات المراقبة والأطباق الدشية</p>
    <p>جودة عالية • أسعار منافسة • خدمة عملاء ممتازة</p>
</div>
""", unsafe_allow_html=True)
