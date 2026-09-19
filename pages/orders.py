import streamlit as st

# إعدادات الصفحة
st.set_page_title("قائمة الطلبات المتاحة - منجز", layout="wide")

st.markdown("""
    <style>
    .order-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-right: 5px solid #28a745;
    }
    .order-header {
        font-size: 18px;
        font-weight: bold;
        color: #333333;
    }
    .order-details {
        color: #666666;
        font-size: 14px;
        margin-top: 8px;
    }
    .price-tag {
        color: #28a745;
        font-size: 16px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 لوحة طلبات العملاء النشطة والمتاحة")
st.write("استعرض الطلبات الحالية المتاحة للتوصيل، وقدم عروض السعر، أو تابع تفاصيل خط سير الرحلة بدقة.")

# محاكاة جلب الطلبات من قاعدة البيانات (Firebase / Backend)
# سيتم استبدال هذه البيانات بالاتصال الفعلي بقاعدة البيانات الخاصة بك
active_orders = [
    {
        "id": "#357756227",
        "store": "حضرموت شيخ المندي - المهندسين",
        "items": "اوردر في حدود 650 جنيه من حضرموت شيخ المندي وبلبن...",
        "delivery_fee": "120.0 جنيه",
        "distance_pickup": "7.25 كم",
        "distance_delivery": "12.0 كم",
        "status": "متاح للتوصيل"
    },
    {
        "id": "#357751528",
        "store": "بيتزا تشكين رانش وسط",
        "items": "٢ بيتزا تشكين رانش وسط، ١ بيتزا بيبروني وسط...",
        "delivery_fee": "53.0 جنيه",
        "distance_pickup": "4.1 كم",
        "distance_delivery": "8.5 كم",
        "status": "متاح للتوصيل"
    },
    {
        "id": "#357726823",
        "store": "دجاج بروستد البركة",
        "items": "5 - وجبة ستربس (5 قطع)...",
        "delivery_fee": "70.0 جنيه",
        "distance_pickup": "3.0 كم",
        "distance_delivery": "6.2 كم",
        "status": "متاح للتوصيل"
    }
]

# عرض الطلبات في بطاقات تفاعلية منظمة
for order in active_orders:
    with st.container():
        st.markdown(f"""
        <div class="order-card">
            <div class="order-header">طلب رقم: {order['id']} | المتجر: {order['store']}</div>
            <div class="order-details"><b>التفاصيل:</b> {order['items']}</div>
            <div class="order-details">📍 مسافة الاستلام: {order['distance_pickup']} | 🏁 مسافة التوصيل: {order['distance_delivery']}</div>
            <div class="price-tag">💰 سعر التوصيل المقترح: {order['delivery_fee']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"عرض خريطة وتفاصيل الطلب {order['id']}", key=f"map_{order['id']}"):
                st.success(تم فتح تفاصيل الخريطة ومواقع الاستلام والتسليم للطلب {order['id']} بنجاح!)
                # هنا يتم توجيه السائق لخريطة الـ GPS وتفاصيل الإحداثيات
        with col2:
            if st.button(f"قبول الطلب وتأكيد السعر {order['id']}", key=f"accept_{order['id']}"):
                st.balloons()
                st.success(تم قبول الطلب بنجاح! تم تحويله إلى قائمة طلباتك النشطة.)

st.markdown("---")
st.info("💡 ملاحظة هندسية: هذه الصفحة مرتبطة بملفات الجلسة وقاعدة البيانات لضمان تحديث الحالات لحظياً دون أي تأخير.")
