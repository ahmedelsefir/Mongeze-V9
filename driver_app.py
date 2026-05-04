import streamlit as st
from datetime import datetime
import json
from pathlib import Path

# إعدادات الصفحة
st.set_page_config(
    page_title="فودي - نسخة المناديل",
    page_icon="🚚",
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
</style>
""", unsafe_allow_html=True)

# العنوان الرئيسي
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="main-title">🚚 فودي</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">نسخة المناديل - توصيل الطلبات</div>', unsafe_allow_html=True)

# خط فاصل
st.markdown("---")

# تسجيل دخول المناديل
st.markdown("### 🔐 تسجيل الدخول")
col1, col2 = st.columns([1, 1])
with col1:
    driver_name = st.text_input(
        "👤 اسم المناديل",
        placeholder="أدخل اسمك",
        key="driver_name"
    )

with col2:
    phone = st.text_input(
        "📱 رقم هاتفك",
        placeholder="رقم الهاتف",
        key="driver_phone"
    )

if driver_name and phone:
    st.success(f"✅ مرحباً بك يا {driver_name}")
    
    # خط فاصل
    st.markdown("---")
    
    # عرض الطلبات المتاحة
    st.markdown("### 📦 الطلبات المتاحة")
    
    try:
        orders_file = Path("delivery_orders.json")
        
        if orders_file.exists():
            with open(orders_file, 'r', encoding='utf-8') as f:
                orders_list = json.load(f)
        else:
            orders_list = []
        
        # الإحصائيات
        my_orders = [o for o in orders_list if o.get("delivery_person") == driver_name]
        available_orders = [o for o in orders_list if o.get("status") == "جاهز للتوصيل 📦" and o.get("delivery_person") is None]
        in_delivery = [o for o in orders_list if o.get("delivery_person") == driver_name and o.get("status") == "قيد التوصيل 🚚"]
        delivered = [o for o in orders_list if o.get("delivery_person") == driver_name and o.get("status") == "تم التوصيل ✅"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 متاح", len(available_orders))
        with col2:
            st.metric("🚚 قيد التوصيل", len(in_delivery))
        with col3:
            st.metric("✅ موصل", len(delivered))
        with col4:
            st.metric("💰 الإجمالي", len(my_orders))
        
        st.markdown("---")
        
        # الطلبات المتاحة
        if available_orders:
            st.markdown("#### 📦 طلبات متاحة للقبول")
            for order in available_orders:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    **رقم الطلب:** {order['order_id']}  
                    **العميل:** {order['customer_name']} - {order['phone']}  
                    **العنوان:** {order['delivery_address']}  
                    **المطعم:** {order['restaurant']}  
                    **وقت التوصيل:** {order['delivery_time']}
                    """)
                
                with col2:
                    if st.button(f"✅ قبول", key=f"accept_{order['order_id']}"):
                        order["delivery_person"] = driver_name
                        order["status"] = "قيد التوصيل 🚚"
                        
                        with open(orders_file, 'w', encoding='utf-8') as f:
                            json.dump(orders_list, f, ensure_ascii=False, indent=2)
                        
                        st.success(f"✅ تم قبول الطلب {order['order_id']}")
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("📭 لا توجد طلبات متاحة حالياً")
        
        # الطلبات قيد التوصيل
        if in_delivery:
            st.markdown("#### 🚚 طلبات قيد التوصيل")
            for order in in_delivery:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"""
                    **رقم الطلب:** {order['order_id']}  
                    **العميل:** {order['customer_name']} - {order['phone']}  
                    **العنوان:** {order['delivery_address']}  
                    **الطلب:** {order['items']}
                    """)
                
                with col2:
                    if st.button(f"✅ وصلت", key=f"delivered_{order['order_id']}"):
                        order["status"] = "تم التوصيل ✅"
                        
                        with open(orders_file, 'w', encoding='utf-8') as f:
                            json.dump(orders_list, f, ensure_ascii=False, indent=2)
                        
                        st.success(f"✅ تم توصيل الطلب {order['order_id']}")
                        st.rerun()
                
                st.markdown("---")
        
        # الطلبات الموصلة
        if delivered:
            st.markdown("#### ✅ طلبات وصلت اليوم")
            st.success(f"🎉 لقد وصلت {len(delivered)} طلب اليوم!")
            for order in delivered:
                st.markdown(f"**{order['order_id']}** - {order['customer_name']} ✅")
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")

else:
    st.warning("⚠️ برجاء إدخال اسمك ورقم هاتفك")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p>🚚 <b>فودي - تطبيق توصيل الطلبات</b></p>
    <p>نسخة المناديل - توصيل آمن وسريع</p>
</div>
""", unsafe_allow_html=True)
