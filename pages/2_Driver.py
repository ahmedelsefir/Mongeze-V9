from utils import send_monjez_email  # 💡 مكان الاستدلال الصحيح في السطر الأول بالملي!
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="منصة مُنجز - بوابة المندوب", layout="wide")

# --- تفعيل الفايربيز ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل ربط السيرفر: {e}")
    db = None

DRIVER_NAME = "ahmed mostafa mohammed"

# --- رادار فحص قائمة الحظر الفورية لمنع النصب والاحتيال ---
if db:
    ban_check = db.collection("banned_users").document(DRIVER_NAME).get()
    if ban_check.exists:
        st.markdown("""
        <div style='background-color: black; padding: 40px; border-radius: 12px; border: 3px solid red; text-align: center; color: white;'>
            <h1 style='color: red;'>🛑 الحساب تائه أو معلق!</h1>
            <h3>عذراً كابتن أحمد، تم تجميد حسابك مؤقتاً لمراجعة تجاوزات مالية.</h3>
            <p style='color: #FFA500;'>يرجى دفع المديونية المتأخرة فوراً أو التواصل الإداري مع مشرف الدعم.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

# --- هيدر الكابتن الموثق ---
st.markdown(f"""
<div style='background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; color: #333;'>
    <img src='https://cdn-icons-png.flaticon.com/512/4128/4128176.png' style='width: 80px; border-radius: 50%;'>
    <h2 style='margin: 10px 0 2px 0;'>{DRIVER_NAME}</h2>
    <p style='color: #EAB308; font-size: 18px; margin: 0;'>⭐⭐⭐⭐⭐</p>
    <span style='background-color: #10B981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;'>✔️ أظهر هوية المرسول - موثق</span>
</div>
""", unsafe_allow_html=True)

# العدادات الإمبراطورية
st.markdown("###")
col_metric1, col_metric2 = st.columns(2)
with col_metric1:
    st.metric(label="📊 الطلبات الموصلة", value="3536 طلبات")
with col_metric2:
    st.metric(label="💰 إجمالي الإيرادات", value="340904.74 جنيه")

st.markdown("---")

# الرصيد المالي السلبي الحقيقي
st.markdown(f"""
<div style='background-color: #FEF2F2; padding: 15px; border-radius: 8px; border: 1px solid #FCA5A5; display: flex; justify-content: space-between; align-items: center; direction: rtl;'>
    <span style='color: #991B1B; font-weight: bold; font-size: 16px;'>📉 رصيد الحساب الحالي:</span>
    <span style='color: #DC2626; font-weight: bold; font-size: 18px;'>-160.96 جنيه</span>
</div>
""", unsafe_allow_html=True)

st.write("#")

driver_tabs = st.tabs(["📥 استلام المزايدات الحية", "📍 الشحنة الحالية والتنفيذ", "🛠️ لوحة مساعدة وإعدادات"])

# --- التبويب الأول: استلام الطلبات من الميدان ---
with driver_tabs[0]:
    st.markdown("#### 📥 الطلبات المتاحة للمزايدة حالياً في الميدان")
    if db:
        live_orders = db.collection("orders").where("status", "==", "processing").stream()
        order_count = 0
        
        for doc in live_orders:
            order_count += 1
            o_data = doc.to_dict()
            o_id = doc.id
            
            st.markdown(f"""
            <div style='background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-right: 4px solid #10B981; margin-bottom: 10px; text-align: right;'>
                <b style='color: #111827;'>📍 طلب توصيل من: {o_data.get('client_name')}</b><br>
                <span style='color: #4B5563;'>📦 تفاصيل الشحنة: {o_data.get('order_details')}</span><br>
                <b style='color: #10B981;'>💵 ميزانية العميل المقترحة: {o_data.get('suggested_price')} جنيه</b>
            </div>
            """, unsafe_allow_html=True)
            
            custom_bid = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=10, value=int(o_data.get('suggested_price', 30)), key=f"num_input_{o_id}")
            if st.button("🚀 إرسال العرض المالي للعميل", key=f"submit_bid_btn_{o_id}", use_container_width=True):
                db.collection("orders").document(o_id).update({
                    "status": "🚖 جاري الاستلام",
                    "driver_assigned": DRIVER_NAME,
                    "suggested_price": custom_bid
                })
                st.success(f"🟢 تم إرسال عرضك بقيمة {custom_bid} جنيه بنجاح! بانتظار العميل.")
                st.rerun()
                
        if order_count == 0:
            st.info("📭 الميدان هادئ الآن. لا توجد طلبات معلقة بانتظار عروض أسعار.")

# --- التبويب الثاني: شاشة التنفيذ والتتبع وإرسال الفواتير ---
with driver_tabs[1]:
    st.markdown("#### 📍 شاشة التنفيذ وتتبع الشحنة الحالية")
    if db:
        active_missions = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).stream()
        mission_count = 0
        
        for doc in active_missions:
            m_data = doc.to_dict()
            m_id = doc.id
            status = m_data.get("status")
            
            if status in ["🚖 جاري الاستلام", "🚚 جاري التوصيل", "✅ في انتظار تقييم الطرفين"]:
                mission_count += 1
                
                st.markdown(f"""
                <div style='background-color: #111827; padding: 20px; border-radius: 10px; color: white; text-align: right; margin-bottom: 15px;'>
                    <h3 style='color: #38BDF8; margin: 0;'>🚚 العميل بانتظارك</h3>
                    <p style='margin: 8px 0;'><b>👤 الاسم:</b> {m_data.get('client_name')}</p>
                    <p style='margin: 8px 0;'><b>📦 محتوى الشحنة:</b> {m_data.get('order_details')}</p>
                    <hr style='border-color: #374151;'>
                    <b style='color: #FBBF24; font-size: 16px;'>💰 القيمة الصافية للرحلة: {m_data.get('suggested_price')}.00 جنيه</b><br>
                    <small style='color: #9CA3AF;'>🚖 حالة الطلب الحالية بالخريطة: {status}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if status == "🚖 جاري الاستلام":
                    if st.button("📦 تم استلام الشحنة والتحرك", key=f"status_btn_pickup_{m_id}", use_container_width=True):
                        db.collection("orders").document(m_id).update({"status": "🚚 جاري التوصيل"})
                        st.rerun()
                        
                elif status == "🚚 جاري التوصيل":
                    if st.button("🏁 إنهاء وتوصيل الطلب بنجاح للوجهة", key=f"status_btn_deliver_{m_id}", use_container_width=True):
                        try:
                            # 1. تحديث قاعدة البيانات أولاً
                            db.collection("orders").document(m_id).update({"status": "✅ في انتظار تقييم الطرفين"})
                            
                            # 2. إرسال الفاتورة السيادية فوراً عبر الإيميل الجديد للعميل تلقائياً
                            invoice_html = f"""
                            <div style="direction: rtl; text-align: right; font-family: sans-serif; border: 1px solid #10B981; padding: 20px; border-radius: 8px;">
                                <h2 style="color: #10B981;">📋 فاتورة رحلة من منصة مُنجز</h2>
                                <p>أهلاً بك يا <b>{m_data.get('client_name')}</b>، تم إنهاء رحلتك بنجاح.</p>
                                <hr>
                                <p><b>👤 الكابتن المسؤول:</b> {DRIVER_NAME}</p>
                                <p><b>📦 الشحنة الموصلة:</b> {m_data.get('order_details')}</p>
                                <p style="font-size: 18px; color: #1E3A8A;"><b>💰 إجمالي الحساب الصافي: {m_data.get('suggested_price')} جنيه</b></p>
                                <hr>
                                <p style="font-size: 12px; color: #6B7280; text-align: center;">شكراً لاستخدامك منصة منجز السيادية 2026 ✨</p>
                            </div>
                            """
                            email_sent = send_monjez_email("ahmed.mustafa@monjez-app.icu", "📦 فاتورة رحلتك وتوصيل شحنتك من منصة مُنجز", invoice_html)
                            
                            if email_sent:
                                st.success("🎯 تم إنهاء المشوار وإرسال الفاتورة الرسمية للعميل بريدياً!")
                            else:
                                st.warning("🎯 تم إنهاء المشوار بنجاح، لكن فشل إرسال الفاتورة بالبريد. يرجى المتابعة يدوياً.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ خطأ أثناء إنهاء الطلب: {e}")
                        
                elif status == "✅ في انتظار تقييم الطرفين":
                    st.warning("🏁 الرحلة وصلت. فضلاً قيّم العميل لإغلاق الحساب وتقييد الأرباح في الخزينة:")
                    rating = st.slider("⭐ تقييم العميل:", 1, 5, 5, key=f"slider_rating_{m_id}")
                    if st.button("💾 حفظ وإغلاق الفاتورة النهائية", key=f"save_final_invoice_{m_id}", use_container_width=True):
                        db.collection("orders").document(m_id).update({"status": "⭐ تم الإغلاق والتقييم بالكامل"})
                        st.success("🎯 تم إغلاق الرحلة وتحويل العمولات والضرائب تلقائياً!")
                        st.rerun()
                        
        if mission_count == 0:
            st.info("🚖 لا توجد لديك أي شحنات أو رحلات نشطة جاري تنفيذها في هذه اللحظة.")

# --- التبويب الثالث ---
with driver_tabs[2]:
    st.markdown("#### 🛠️ مركز المساعدة والدعم المباشر للمناديب")
    st.caption("تواصل مباشر مع مشرفي النظام للإبلاغ عن المشاكل أو لتوثيق الفواتير الكاش.")
