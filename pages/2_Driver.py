import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="بوابة السائق - تقديم العروض", layout="wide")

# --- 2. تفعيل قاعدة البيانات بنظام الأمان العالي ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    db = None

# --- 3. الهيدر وصورة المندوب الافتراضية ---
col_img, col_info = st.columns([1, 5])
with col_img:
    st.markdown("""
    <img src="https://www.w3schools.com/howto/img_avatar.png" 
         style="width:80px; border-radius:50%; border: 3px solid #00A86B;">
    """, unsafe_allow_html=True)
with col_info:
    st.markdown("<h2 style='margin:0;'>مرحباً بك، كابتن أحمد 🚖</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#666;'>بوابة الفحص وتقديم عروض الأسعار الفورية لعام 2026</p>", unsafe_allow_html=True)

st.markdown("---")

# --- 4. تقسيم الصفحة لتبويبات (الطلبات الحية / الإعدادات) ---
tab_offers, tab_driver_settings = st.tabs(["📋 طلبات المزايدة الحية", "⚙️ إعدادات السائق والتنبيهات"])

with tab_offers:
    st.subheader("📥 الطلبات المتاحة للمزايدة حالياً:")
    
    if db is not None:
        try:
            # جلب الطلبات النشطة التي تنتظر عروض الأسعار
            orders_ref = db.collection("orders").where("status", "==", "processing").stream()
            has_orders = False
            
            for order in orders_ref:
                has_orders = True
                order_data = order.to_dict()
                order_id = order.id
                
                # عرض كارت الطلب بالتفاصيل والميزانية المقترحة من العميل
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 18px; border-radius: 10px; margin-bottom: 15px; 
                            box-shadow: 0 4px 8px rgba(0,0,0,0.05); border-right: 5px solid #00A86B; color: #333;'>
                    <h4 style='margin: 0; color:#111;'>📍 طلب توصيل من: {order_data.get('client_name', 'عميل غير معروف')}</h4>
                    <p style='margin: 10px 0;'>📦 <b>تفاصيل الشحنة:</b> {order_data.get('order_details', '')}</p>
                    <p style='margin: 0; color: #00A86B; font-weight: bold;'>💰 ميزانية العميل المقترحة: {order_data.get('suggested_price', 0)} جنيه</p>
                </div>
                """, unsafe_allow_html=True)
                
                # نموذج تقديم السعر المخصص داخل الكارت
                with st.container():
                    col_price, col_btn = st.columns([1, 1])
                    with col_price:
                        # السائق يقدم سعره الخاص بناءً على المسافة وظروف الطريق
                        driver_bid = st.number_input(
                            "اكتب عرض السعر الخاص بك (جنيه)", 
                            min_value=10, 
                            value=int(order_data.get('suggested_price', 30)) + 5, 
                            key=f"bid_val_{order_id}"
                        )
                    with col_btn:
                        st.write("#") # وزن محاذاة الزر
                        if st.button("🚀 إرسال العرض المالي للعميل", key=f"submit_bid_{order_id}", use_container_width=True):
                            # تسجيل العرض المالي داخل مجموعة فرعية تابعة للطلب نفسه
                            db.collection("orders").document(order_id).collection("bids").add({
                                "driver_name": "الكابتن أحمد",
                                "driver_phone": "+20 123 456 789",
                                "proposed_price": driver_bid,
                                "timestamp": firestore.SERVER_TIMESTAMP
                            })
                            st.success(f"🟢 تم إرسال عرضك بقيمة {driver_bid} جنيه بنجاح! بانتظار موافقة العميل.")
                st.markdown("---")
                
            if not has_orders:
                st.info("📭 لا توجد طلبات جديدة تحتاج عروض أسعار حالياً.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء جلب الطلبات: {e}")

with tab_driver_settings:
    st.subheader("⚙️ إعدادات الملف الشخصي والتنبيهات الفورية للسائق")
    st.text_input("📱 رقم الهاتف المحمول المعتمد", value="+20 123 456 789")
    driver_notif = st.toggle("🔔 تفعيل صوت التنبيهات الفورية عند ورود طلب جديد", value=True)
    if driver_notif:
        st.caption("🟢 نظام التنبيهات نشط: سيقوم السيرفر بإطلاق إشعار فور نشر عميل لطلب في منطقتك.")
    else:
        st.caption("⚪ التنبيهات معطلة.")
    
    if st.button("💾 حفظ إعدادات السائق"):
        st.success("تم تحديث وحفظ إعدادات حسابك بنجاح على السيرفر.")
