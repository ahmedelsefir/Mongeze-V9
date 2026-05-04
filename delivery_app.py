import streamlit as st
from datetime import datetime
import random

# إعدادات الصفحة
st.set_page_config(
    page_title="تطبيق الخدمات",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS مخصص
st.markdown("""
<style>
    * {
        direction: rtl;
        text-align: right;
    }
    
    body {
        background-color: #f5f5f5;
    }
    
    /* Header */
    .header-container {
        background-color: white;
        padding: 1rem;
        border-bottom: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0;
    }
    
    .header-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        text-align: center;
        flex: 1;
    }
    
    /* Banner أصفر */
    .yellow-banner {
        background-color: #ffd700;
        padding: 1.2rem;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        border-radius: 0;
    }
    
    .yellow-banner-text {
        font-size: 0.95rem;
        font-weight: 500;
        color: #333;
        line-height: 1.5;
    }
    
    /* Filter Buttons */
    .filter-container {
        display: flex;
        gap: 0.8rem;
        padding: 1rem;
        background-color: white;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .filter-btn {
        padding: 0.6rem 1.2rem;
        border: 2px solid #ddd;
        background-color: white;
        border-radius: 20px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s;
        font-size: 0.9rem;
    }
    
    .filter-btn:hover {
        border-color: #00b894;
        color: #00b894;
    }
    
    .filter-btn.active {
        background-color: #00b894;
        color: white;
        border-color: #00b894;
    }
    
    /* بطاقة الطلب */
    .order-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .order-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .order-avatar {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #00d4a4 0%, #00b894 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        position: relative;
    }
    
    .order-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 0.3rem;
    }
    
    .order-subtitle {
        font-size: 0.85rem;
        color: #00d4a4;
        margin-bottom: 0.5rem;
    }
    
    .order-detail {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    
    .service-type-badge {
        display: inline-block;
        background-color: #e8f5e9;
        color: #00b894;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    /* معلومات المسافة والسعر */
    .distance-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1rem 0;
        padding: 0.8rem 0;
        border-top: 1px solid #eee;
        border-bottom: 1px solid #eee;
    }
    
    .info-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
        text-align: center;
    }
    
    .info-value {
        font-weight: bold;
        font-size: 0.95rem;
        color: #333;
    }
    
    .info-label {
        font-size: 0.8rem;
        color: #999;
    }
    
    /* الأزرار */
    .buttons-container {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .btn-accept {
        background-color: #00b894;
        color: white;
        border: none;
        padding: 0.8rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
        cursor: pointer;
        flex: 1;
        transition: background-color 0.3s;
    }
    
    .btn-accept:hover {
        background-color: #009373;
    }
    
    .btn-other {
        background-color: #ffd700;
        color: #333;
        border: none;
        padding: 0.8rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
        cursor: pointer;
        flex: 1;
        transition: background-color 0.3s;
    }
    
    .btn-other:hover {
        background-color: #ffed4e;
    }
    
    /* Price range */
    .price-range {
        font-size: 0.85rem;
        color: #999;
        margin-top: 0.5rem;
        text-align: center;
    }
    
    /* Bottom Navigation */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        border-top: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-around;
        padding: 0.5rem 0;
        box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
        z-index: 100;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 0.3rem;
        padding: 0.5rem;
        cursor: pointer;
        flex: 1;
    }
    
    .nav-item-icon {
        font-size: 1.5rem;
    }
    
    .nav-item-label {
        font-size: 0.75rem;
        color: #999;
    }
    
    .nav-item.active .nav-item-label {
        color: #00b894;
    }
    
    .nav-item.active .nav-item-icon {
        color: #00b894;
    }
    
    /* Main content padding */
    .main-content {
        padding-bottom: 80px;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'selected_service_type' not in st.session_state:
    st.session_state.selected_service_type = 'الكل'

# البيانات المتاحة - مع أنواع الخدمات
services_data = [
    {
        "id": 1,
        "title": "3 طلبات \"جميع الخدمات\"",
        "details": "قطعتين بروستد مع أرز\nخمس قطع استريس",
        "location": "شاهين (سلعتين)",
        "current_location": "13.7 كم",
        "delivery_location": "2.0 كم",
        "price": "25.00",
        "price_range": "من 25 جنيه إلى 35 جنيه",
        "request_id": "#352896514",
        "service_type": "توصيل طعام",
        "icon": "🍔"
    },
    {
        "id": 2,
        "title": "طلب توصيل عاجل",
        "details": "2سيناريون شوكولاون",
        "location": "شاهين (حي)",
        "current_location": "11.4 كم",
        "delivery_location": "21.0 كم",
        "price": "118.00",
        "price_range": "من 118 جنيه إلى 165 جنيه",
        "request_id": "#352896514",
        "service_type": "توصيل سريع",
        "icon": "⚡"
    },
    {
        "id": 3,
        "title": "خدمة تصليح",
        "details": "قطعة دجاج مع بطاطا",
        "location": "حي النيل",
        "current_location": "8.5 كم",
        "delivery_location": "3.2 كم",
        "price": "45.50",
        "price_range": "من 40 جنيه إلى 50 جنيه",
        "request_id": "#352896515",
        "service_type": "تصليح",
        "icon": "🔧"
    },
    {
        "id": 4,
        "title": "توصيل أغراض منزلية",
        "details": "أسطوانة غاز + تنظيفات",
        "location": "الزيتون",
        "current_location": "6.3 كم",
        "delivery_location": "1.5 كم",
        "price": "35.00",
        "price_range": "من 30 جنيه إلى 40 جنيه",
        "request_id": "#352896516",
        "service_type": "توصيل عام",
        "icon": "📦"
    },
    {
        "id": 5,
        "title": "خدمة تنظيف",
        "details": "تنظيف شقة كاملة",
        "location": "مدينة نصر",
        "current_location": "9.2 كم",
        "delivery_location": "2.8 كم",
        "price": "80.00",
        "price_range": "من 75 جنيه إلى 85 جنيه",
        "request_id": "#352896517",
        "service_type": "تنظيف",
        "icon": "🧹"
    },
    {
        "id": 6,
        "title": "توصيل طعام من مطعم",
        "details": "ساندوتشات + عصيرات",
        "location": "الهرم",
        "current_location": "15.1 كم",
        "delivery_location": "3.5 كم",
        "price": "55.00",
        "price_range": "من 50 جنيه إلى 60 جنيه",
        "request_id": "#352896518",
        "service_type": "توصيل طعام",
        "icon": "🍔"
    }
]

# الحصول على أنواع الخدمات المتاحة
service_types = list(set([s['service_type'] for s in services_data]))

# Header
header_col1, header_col2, header_col3 = st.columns([1, 3, 1])

with header_col1:
    if st.button("< إيقاف", key="back_btn", use_container_width=True):
        st.session_state.current_page = 'menu'

with header_col2:
    st.markdown('<div class="header-title">الرئيسية</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #00d4a4; font-size: 0.85rem;">التنبيهات مفعلة</div>', unsafe_allow_html=True)

with header_col3:
    st.markdown("🏆")

# Yellow Banner
st.markdown("""
<div class="yellow-banner">
    <span style="font-size: 1.5rem;">◄</span>
    <div class="yellow-banner-text">
        <strong>جرب نظام إسناد الخدمات الجديد</strong> للحصول على الطلبات بسرعة وسهولة. انقر هنا للبدء
    </div>
</div>
""", unsafe_allow_html=True)

# Filter Section
st.markdown("""
<div class="filter-container">
""", unsafe_allow_html=True)

# Create filter buttons
col = st.columns(5)
filter_options = ['الكل'] + sorted(service_types)

for idx, service in enumerate(filter_options):
    with col[idx % 5]:
        if st.button(
            service,
            key=f"filter_{service}",
            use_container_width=True
        ):
            st.session_state.selected_service_type = service

st.markdown("</div>", unsafe_allow_html=True)

# Main Content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Filter the services
if st.session_state.selected_service_type == 'الكل':
    filtered_services = services_data
else:
    filtered_services = [s for s in services_data if s['service_type'] == st.session_state.selected_service_type]

# عرض الخدمات
if filtered_services:
    for service in filtered_services:
        st.markdown(f"""
        <div class="order-card">
            <div class="order-header">
                <div style="flex: 1;">
                    <div class="order-title">{service['icon']} {service['title']}</div>
                    <div class="order-subtitle">خدمة مفعلة</div>
                </div>
                <div class="order-avatar">
                    {service['id']}
                    <span style="position: absolute; width: 12px; height: 12px; background-color: #ff4444; border-radius: 50%; top: 0; right: 0; border: 2px solid white;"></span>
                </div>
            </div>
            
            <div class="service-type-badge">{service['service_type']}</div>
            
            <div class="order-detail">
                {service['details']}
            </div>
            
            <div style="font-size: 0.9rem; color: #00d4a4; margin: 0.5rem 0; font-weight: 500;">
                📍 {service['location']}
            </div>
            
            <div class="distance-info">
                <div class="info-item">
                    <span>🚗</span>
                    <div>
                        <div class="info-value">{service['current_location']}</div>
                        <div class="info-label">قطع الحالي</div>
                    </div>
                </div>
                <div class="info-item">
                    <span>📦</span>
                    <div>
                        <div class="info-value">{service['delivery_location']}</div>
                        <div class="info-label">موقع الالتقاط</div>
                    </div>
                </div>
                <div class="info-item">
                    <span>🚩</span>
                    <div>
                        <div class="info-value">{service['delivery_location']}</div>
                        <div class="info-label">موقع التسليم</div>
                    </div>
                </div>
            </div>
            
            <div class="buttons-container">
                <button class="btn-accept">اريح {service['price']} جنيه</button>
                <button class="btn-other">عرض آخر</button>
            </div>
            
            <div class="price-range">{service['price_range']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("❌ لا توجد خدمات متاحة في هذه الفئة حالياً")

st.markdown('</div>', unsafe_allow_html=True)

# Bottom Navigation
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item active">
        <div class="nav-item-icon">💚</div>
        <div class="nav-item-label">الرئيسية</div>
    </div>
    <div class="nav-item">
        <div class="nav-item-icon">🔧</div>
        <div class="nav-item-label">الخدمات</div>
    </div>
    <div class="nav-item">
        <div class="nav-item-icon">🏠</div>
        <div class="nav-item-label">المناويب</div>
    </div>
    <div class="nav-item">
        <div class="nav-item-icon">🚨</div>
        <div class="nav-item-label">التنبيهات</div>
    </div>
    <div class="nav-item">
        <div class="nav-item-icon">👤</div>
        <div class="nav-item-label">صفحتي</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Custom spacing
st.markdown("<br>" * 5, unsafe_allow_html=True)
