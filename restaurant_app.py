import streamlit as st
from datetime import datetime
import json
from pathlib import Path

# إعدادات الصفحة
st.set_page_config(
    page_title="فودي - نسخة المطاعم",
    page_icon="🍽️",
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
    
    .order-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-title">🍽️ فودي</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">نسخة المطاعم - إدارة الطلبات</div>', unsafe_allow_html=True)

# خط فاصل
st.markdown("---")

# تسجيل دخول المطاعم
st.markdown("### 🔐 تسجيل الدخول")
col1, col2 = st.columns([2, 1])
with col1:
    restaurant_name = st.selectbox(
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
    manager_name = st.text_input(
        "👤 اسم المدير",
        placeholder="اسمك",
        key="manager"
    )

if restaurant_name and manager_name:
    rest_short_name = restaurant_name.split()[0]
    st.success(f"✅ مرحباً بك يا {manager_name} في {restaurant_name}")
    
    # خط فاصل
    st.markdown("---")
    
    # عرض الطلبات الخاصة بهذا المطعم
    st.markdown("### 📦 الطلبات الخاصة بك")
    
    try:
        orders_file = Path("delivery_orders.json")
        
        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders_list = json.load(f)
        else:
            orders_list = []
        
        # تصفية الطلبات الخاصة بهذا المطعم
        restaurant_orders = [order for order in orders_list if order.get("restaurant") == rest_short_name]
        
        if restaurant_orders:
            # الإحصائيات
            pending_count = len([o for o in restaurant_orders if o.get("status") == "قيد الانتظار ⏳"])
            preparing_count = len([o for o in restaurant_orders if o.get("status") == "قيد التحضير 👨‍🍳"])
            ready_count = len([o for o in restaurant_orders if o.get("status") == "جاهز للتوصيل 📦"])
            delivered_count = len([o for o in restaurant_orders if o.get("status") == "تم التوصيل ✅"])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏳ جديد", pending_count)
            with col2:
                st.metric("👨‍🍳 قيد التحضير", preparing_count)
            with col3:
                st.metric("📦 جاهز", ready_count)
            with col4:
                st.metric("✅ موصل", delivered_count)
            
            st.markdown("---")
            
            # الطلبات الجديدة
            pending = [o for o in restaurant_orders if o.get("status") == "قيد الانتظار ⏳"]
            if pending:
                st.markdown("#### ⏳ طلبات جديدة")
                for order in pending:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **رقم الطلب:** {order['order_id']}  
                        **العميل:** {order['customer_name']} - {order['phone']}  
                        **الطلب:** {order['items']}  
                        **ملاحظات:** {order['notes'] if order['notes'] else 'لا توجد'}  
                        **الموعد:** {order['delivery_time']}
                        """)
                    
                    with col2:
                        if st.button(f"��‍🍳 قيد التحضير", key=f"prep_{order['order_id']}"):
                            order["status"] = "قيد التحضير 👨‍🍳"
                            
                            with open(orders_file, 'w', encoding='utf-8') as f:
                                json.dump(orders_list, f, ensure_ascii=False, indent=2)
                            
                            st.success(f"✅ بدأنا تحضير الطلب {order['order_id']}")
                            st.rerun()
                    
                    st.markdown("---")
            
            # الطلبات قيد التحضير
            preparing = [o for o in restaurant_orders if o.get("status") == "قيد التحضير 👨‍🍳"]
            if preparing:
                st.markdown("#### 👨‍🍳 قيد التحضير")
                for order in preparing:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **رقم الطلب:** {order['order_id']}  
                        **العميل:** {order['customer_name']} - {order['phone']}  
                        **الطلب:** {order['items']}
                        """)
                    
                    with col2:
                        if st.button(f"📦 جاهز", key=f"ready_{order['order_id']}"):
                            order["status"] = "جاهز للتوصيل 📦"
                            
                            with open(orders_file, 'w', encoding='utf-8') as f:
                                json.dump(orders_list, f, ensure_ascii=False, indent=2)
                            
                            st.success(f"✅ الطلب {order['order_id']} جاهز!")
                            st.rerun()
                    
                    st.markdown("---")
            
            # الطلبات الجاهزة للتوصيل
            ready = [o for o in restaurant_orders if o.get("status") == "جاهز للتوصيل 📦"]
            if ready:
                st.markdown("#### 📦 جاهز للتوصيل")
                for order in ready:
                    st.markdown(f"""
                    **رقم الطلب:** {order['order_id']}  
                    **العميل:** {order['customer_name']} - {order['phone']}  
                    **العنوان:** {order['delivery_address']}  
                    **في انتظار مناديل**
                    """)
                    st.markdown("---")
            
            # الطلبات الموصلة
            delivered = [o for o in restaurant_orders if o.get("status") == "تم التوصيل ✅"]
            if delivered:
                st.markdown("#### ✅ طلبات موصلة اليوم")
                st.success(f"تم توصيل {len(delivered)} طلب بنجاح اليوم")
        
        else:
            st.info("✅ لا توجد طلبات حالياً")
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")

else:
    st.warning("⚠️ برجاء اختيار المطعم واسم المدير")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p>🍽️ <b>فودي - تطبيق توصيل الطلبات</b></p>
    <p>نسخة المطاعم - إدارة وتحضير الطلبات</p>
</div>
""", unsafe_allow_html=True)
