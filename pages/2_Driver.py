import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="بوابة السائق الاحترافية - منجز", layout="wide")

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

# --- 3. إدارة حالات الجلسة والتنقل الديناميكي ---
if "current_step" not in st.session_state:
    st.session_state.current_step = "view_orders"
if "active_order_id" not in st.session_state:
    st.session_state.active_order_id = None

# --- 4. الهيدر الاحترافي وصورة المندوب (Profile Header) ---
# هنا قمنا بتصميم كارت علوي يعرض بيانات كابتن التوصيل وصورته الشخصية لثقة تامة في النظام
col_img, col_info = st.columns([1, 5])
with col_img:
    # صورة افتراضية للمندوب بأسلوب دائري احترافي
    st.markdown("""
    <img src="https://www.w3schools.com/howto/img_avatar.png" 
         style="width:85px; border-radius:50%; border: 3px solid #00A86B; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    """, unsafe_allow_html=True)
with col_info:
    st.markdown("<h2 style='margin:0; color:#111;'>مرحباً بك، كابتن أحمد 🚖</h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#666;'>حالة الحساب: <span style='color:#00A86B; font-weight:bold;'>نشط ومستعد</span> | المعرف: #353374</p>", unsafe_allow_html=True)

st.markdown("---")

# --- 5. نظام التبويبات الذكي (Tabs) لمحاكاة أزرار التطبيق السفلى ---
# هذا التقسيم يمنع تشتيت السائق ويجعل الوصول للمعلومات فوري وسريع (Scannable)
tab_main, tab_history, tab_settings = st.tabs(["📋 الطلبات الحية", "📊 الأرباح والمناوبات", "⚙️ إعدادات الحساب"])

# ##########################################
# التبويب الأول: إدارة الطلبات والرحلة الحالية
# ##########################################
with tab_main:
    if st.session_state.current_step == "view_orders":
        st.subheader("📥 الطلبات المتاحة حالياً في انتظارك:")
        
        if db is not None:
            try:
                # جلب الطلبات النشطة فقط
                orders_ref = db.collection("orders").where("status", "==", "processing").stream()
                has_orders = False
                
                for order in orders_ref:
                    has_orders = True
                    order_data = order.to_dict()
                    order_id = order.id
                    
                    # تصميم كارت الرحلة الشامل (المسافات والأرباح المتوقعة)
                    st.markdown(f"""
                    <div style='background-color: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 15px; 
                                box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-right: 6px solid #00A86B; color: #333;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <h4 style='margin: 0; color:#111;'>📍 طلب توصيل رقم: #{order_id[:6]}</h4>
                            <span style='background-color: #00A86B; color: #fff; padding: 5px 12px; border-radius: 8px; font-weight: bold;'>
                                اربح 35.00 جنيه
                            </span>
                        </div>
                        <p style='margin: 12px 0; font-size: 15px;'>📦 <b>محتويات الطلب:</b> {order_data.get('order_details', '')}</p>
                        <div style='font-size: 13px; color: #666; background-color: #f9f9f9; padding: 8px; border-radius: 6px;'>
                            🛣️ موقع الاستلام: 2.15 كم | 🏁 موقع التسليم: 4.0 كم
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🤝 قبول وإسناد الطلب إليّ", key=f"accept_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).update({"status": "🚖 جاري الاستلام"})
                        st.session_state.active_order_id = order_id
                        st.session_state.current_step = "track_trip"
                        st.rerun()
                        
                if not has_orders:
                    st.info("📭 لا توجد طلبات جديدة في منطقتك حالياً. ابقَ متصلاً!")
            except Exception as e:
                st.error(f"خطأ في جلب البيانات: {e}")

    elif st.session_state.current_step == "track_trip":
        st.subheader("📍 شاشة التنفيذ وتتبع الشحنة الحالية")
        active_id = st.session_state.active_order_id
        
        if db is not None and active_id is not None:
            doc = db.collection("orders").document(active_id).get()
            if doc.exists:
                order_data = doc.to_dict()
                
                # واجهة تتبع الرحلة باللون الداكن الفخم لجذب التركيز أثناء القيادة
                st.markdown(f"""
                <div style='background-color: #1e293b; padding: 25px; border-radius: 15px; color: #fff; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.15);'>
                    <h3 style='color: #38bdf8; margin: 0;'>🚚 العميل بانتظارك</h3>
                    <p style='font-size: 18px; margin: 15px 0;'>👤 <b>الاسم:</b> {order_data.get('client_name', 'غير معروف')}</p>
                    <p style='font-size: 16px; color: #cbd5e1;'>📦 <b>محتوى الشحنة:</b> {order_data.get('order_details', '')}</p>
                    <div style='border-top: 1px solid #334155; margin-top:15px; padding-top:10px; color:#4ade80;'>
                        💰 القيمة الصافية للرحلة: 35.00 جنيه
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📦 تم استلام الشحنة من المتجر", use_container_width=True):
                        db.collection("orders").document(active_id).update({"status": "🚚 جاري التوصيل للعميل"})
                        st.success("تم تحديث الحالة، توجه إلى موقع التسليم.")
                with col2:
                    if st.button("🏁 إنهاء وتوصيل الطلب بنجاح", use_container_width=True):
                        db.collection("orders").document(active_id).update({"status": "✅ تم التسليم بنجاح"})
                        st.balloons()
                        st.session_state.current_step = "view_orders"
                        st.session_state.active_order_id = None
                        st.success("تم قفل الرحلة وإضافة الأرباح لمحفظتك!")
                        st.rerun()

# ##########################################
# التبويب الثاني: إحصائيات الأرباح والمناوبات
# ##########################################
with tab_history:
    st.subheader("📊 تقرير الأداء المالي والمناوبات")
    
    # بطاقات عرض رقمية سريعة القراءة لعام 2026
    c1, c2, c3 = st.columns(3)
    c1.metric(label="إيرادات اليوم", value="105.00 جنيه", delta="+35.00")
    c2.metric(label="الطلبات المكتملة", value="3 رحلات", delta="1")
    c3.metric(label="ساعات العمل اليومية", value="4.5 ساعة")
    
    st.markdown("""
    <div style='background-color:#f8fafc; padding:15px; border-radius:10px; border-left:4px solid #3b82f6;'>
        💡 <b>ملاحظة النظام:</b> مناوبتك الحالية تنتهي الساعة 11:00 مساءً. حافظ على تقييمك المرتفع للحصول على حوافز إضافية!
    </div>
    """, unsafe_allow_html=True)

# ##########################################
# التبويب الثالث: إعدادات وثائق الحساب
# ##########################################
with tab_settings:
    st.subheader("⚙️ إعدادات الحساب وسياسات التشغيل")
    
    # نموذج لتحديث بيانات السائق بشكل آمن
    with st.form("driver_profile_form"):
        st.text_input("رقم الهاتف المحمول", value="+20 123 456 789")
        st.text_input("رقم رخصة القيادة المعتمدة", value="🎯 LIC-2026-9938")
        vehicle_type = st.selectbox("نوع وسيلة النقل", ["دراجة نارية (موتوسيكل)", "سيارة ملاكي", "سكوتر كهربائي"])
        
        save_profile = st.form_submit_button("💾 حفظ التحديثات")
        if save_profile:
            st.success("تم تحديث وثائق وبيانات الحساب على السيرفر الآمن بنجاح.")
