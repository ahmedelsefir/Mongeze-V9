import streamlit as st
from datetime import datetime
import json
from pathlib import Path

# إعدادات الصفحة
st.set_page_config(
    page_title="فودي - تطبيق توصيل الطلبات",
    page_icon="🍔",
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
        color: #FF6B35;
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
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
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
    st.markdown('<div class="main-title">🍔 فودي</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">توصيل الطلبات في دقائق</div>', unsafe_allow_html=True)

# خط فاصل
st.markdown("---")

# معلومات المطاعم المتاحة
st.markdown("### 🏪 المطاعم المتاحة")
col1, col2, col3, col4 = st.columns(4)

restaurants_info = [
    ("🍔", "برجر كنج", "برجر وفرايز"),
    ("🍕", "بيتزا هت", "بيتزا شهية"),
    ("🍗", "تشكن الذيذ", "دجاج مشوي"),
    ("🍜", "شاورما الشام", "شاورما ولحمة")
]

with col1:
    st.info(f"{restaurants_info[0][0]} **{restaurants_info[0][1]}**\n{restaurants_info[0][2]}")
with col2:
    st.info(f"{restaurants_info[1][0]} **{restaurants_info[1][1]}**\n{restaurants_info[1][2]}")
with col3:
    st.info(f"{restaurants_info[2][0]} **{restaurants_info[2][1]}**\n{restaurants_info[2][2]}")
with col4:
    st.info(f"{restaurants_info[3][0]} **{restaurants_info[3][1]}**\n{restaurants_info[3][2]}")

st.markdown("---")

# النموذج الرئيسي
st.markdown("### ✍️ نموذج الطلب")

with st.form("delivery_order", clear_on_submit=True):
    
    # الصف الأول
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input(
            "👤 الأسم بالكامل",
            placeholder="أدخل اسمك الكامل",
            key="name"
        )
    with col2:
        phone_number = st.text_input(
            "📱 رقم الهاتف",
            placeholder="أدخل رقم الهاتف (مثال: 201012345678)",
            key="phone"
        )
    
    # الصف الثاني
    col1, col2 = st.columns(2)
    with col1:
        restaurant = st.selectbox(
            "🏪 اختر المطعم",
            [
                "برجر كنج 🍔",
                "بيتزا هت 🍕",
                "تشكن الذيذ 🍗",
                "شاورما الشام 🍜"
            ],
            key="restaurant"
        )
    with col2:
        delivery_time = st.selectbox(
            "⏱️ وقت التوصيل المفضل",
            [
                "في أسرع وقت ممكن ⚡",
                "بعد 30 دقيقة",
                "بعد 1 ساعة",
                "بعد 2 ساعة"
            ],
            key="time"
        )
    
    # الصف الثالث
    col1, col2 = st.columns(2)
    with col1:
        order_items = st.text_area(
            "🍽️ قائمة الطلب",
            placeholder="مثال:\n- برجر بيج 2x\n- فرايز وسط 1x\n- كولا 2x\n- موتزاريلا استيك",
            height=100,
            key="items"
        )
    with col2:
        delivery_address = st.text_area(
            "📍 عنوان التوصيل",
            placeholder="أدخل العنوان كاملاً:\n- المحافظة\n- المدينة\n- الشارع\n- رقم العمارة/البيت\n- نقطة مرجعية",
            height=100,
            key="address"
        )
    
    # الملاحظات الإضافية
    notes = st.text_area(
        "📝 ملاحظات إضافية (اختيارية)",
        placeholder="مثال: بدون بصل، إضافة صلصة حارة...",
        height=70,
        key="notes"
    )
    
    # زر الإرسال
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submit_button = st.form_submit_button(
            "✅ تأكيد الطلب",
            use_container_width=True
        )

# معالجة الطلب
if submit_button:
    # التحقق من البيانات
    if not customer_name or not customer_name.strip():
        st.error("❌ برجاء إدخال اسمك الكامل")
        st.stop()
    
    if not phone_number or not phone_number.strip():
        st.error("❌ برجاء إدخال رقم الهاتف")
        st.stop()
    
    # التحقق من صيغة رقم الهاتف
    phone_clean = phone_number.strip()
    if not phone_clean.isdigit() or len(phone_clean) < 10:
        st.error("❌ رقم الهاتف غير صحيح. يجب أن يكون رقماً بـ 10 أرقام على الأقل")
        st.stop()
    
    if not delivery_address or not delivery_address.strip():
        st.error("❌ برجاء إدخال عنوان التوصيل بالتفصيل")
        st.stop()
    
    if not order_items or not order_items.strip():
        st.error("❌ برجاء إدخال الطلبات")
        st.stop()
    
    # إذا كانت جميع البيانات صحيحة
    order_data = {
        "customer_name": customer_name.strip(),
        "phone": phone_number.strip(),
        "restaurant": restaurant.split()[0],  # إزالة الإيموجي
        "items": order_items.strip(),
        "delivery_address": delivery_address.strip(),
        "delivery_time": delivery_time,
        "notes": notes.strip(),
        "status": "تم استقبال الطلب ✅",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # حفظ البيانات
    try:
        orders_file = Path("delivery_orders.json")
        orders_list = []
        
        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders_list = json.load(f)
        
        orders_list.append(order_data)
        
        with open(orders_file, 'w', encoding='utf-8') as f:
            json.dump(orders_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"⚠️ تم استلام طلبك لكن حدثت مشكلة في الحفظ: {str(e)}")
    
    # رسالة النجاح
    st.success(f"✅ تم استقبال طلبك بنجاح يا {customer_name}!")
    st.info(f"📞 سيتم التوصيل خلال وقت قصير على الرقم: {phone_number}")
    st.balloons()
    
    # عرض ملخص الطلب
    st.markdown("### 📄 ملخص طلبك:")
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.write(f"**👤 الأسم:** {customer_name}")
        st.write(f"**📱 الهاتف:** {phone_number}")
        st.write(f"**🏪 المطعم:** {restaurant}")
    
    with summary_col2:
        st.write(f"**⏱️ وقت التوصيل:** {delivery_time}")
        st.write(f"**🍽️ الطلب:**")
        st.code(order_items)
    
    st.write(f"**📍 العنوان:** {delivery_address}")
    if notes:
        st.write(f"**📝 ملاحظات:** {notes}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p>🍔 <b>فودي - تطبيق توصيل الطلبات</b></p>
    <p>اطلب من أفضل المطاعم وسيصل إليك بسرعة</p>
    <p>سرعة التوصيل • أسعار منخفضة • جودة عالية</p>
    <p style="font-size: 0.8rem; margin-top: 1rem;">استخدم فودي الآن واستمتع بتجربة توصيل رائعة</p>
</div>
""", unsafe_allow_html=True)
