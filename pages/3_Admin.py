import html as html_mod
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore

st.set_page_config(page_title="غرفة العمليات والرقابة - منجز", layout="wide")

# --- تفعيل قاعدة البيانات السحابية ---
db = init_firestore()
if db is None:
    st.error("❌ فشل الاتصال بقاعدة البيانات")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🛡️ مركز الرقابة وغرفة العمليات المركزية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563;'>نظام إدارة المشرفين، الموظفين، وبلاغات الدعم الفني، واعتماد مستندات السائقين والربط الأمني للعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

st.sidebar.markdown("### 🔐 بوابة تسجيل دخول الموظفين")
user_role = st.sidebar.selectbox("اختر رتبتك الإدارية للمعاينة:", ["المدير العام (Super Admin)", "مشرف (Supervisor)", "موظف دعم فني (Support Agent)"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ الإعدادات المالية")
COMMISSION_RATE = st.sidebar.slider("نسبة عمولة المنصة (%)", 1, 50, 10) / 100
VAT_RATE = st.sidebar.slider("ضريبة القيمة المضافة (%)", 1, 30, 14) / 100

tab_support, tab_drivers_kyc, tab_finance, tab_staff, tab_ban_list = st.tabs([
    "🚨 مركز الدعم الفني", 
    "🚗 اعتماد مستندات السائقين", 
    "📊 دفتر الحسابات والضرائب", 
    "👥 الهيكل الوظيفي", 
    "🚫 القائمة السوداء"
])

# --- التبويب الأول: مركز الدعم ومكافحة الاحتيال المربوط بالحظر ---
with tab_support:
    st.subheader("🚩 بلاغات التجاوز والنزاعات النشطة")
    
    if db is not None:
        try:
            tickets_ref = db.collection("support_tickets").where("resolved", "==", False).stream()
            has_tickets = False
            
            for ticket in tickets_ref:
                has_tickets = True
                t_data = ticket.to_dict()
                t_id = ticket.id
                accused = t_data.get('accused_name')
                
                st.markdown(f"""
                <div style='background-color: #FEF2F2; padding: 18px; border-radius: 10px; margin-bottom: 12px; 
                            border-right: 5px solid #DC2626; color: #333; text-align: right;'>
                    <b style='color: #DC2626; font-size: 16px;'>🚨 بلاغ عن: {html_mod.escape(str(t_data.get('type', '')))}</b>
                    <p style='margin: 5px 0;'><b>👤 الشاكي:</b> {html_mod.escape(str(t_data.get('reporter_name', '')))} ({html_mod.escape(str(t_data.get('reporter_role', '')))})</p>
                    <p style='margin: 5px 0;'><b>⚠️ المشكو في حقه:</b> {html_mod.escape(str(accused))} ({html_mod.escape(str(t_data.get('accused_role', '')))})</p>
                    <p style='margin: 5px 0;'><b>📝 تفاصيل الواقعة:</b> {html_mod.escape(str(t_data.get('details', '')))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_act1, col_act2, col_act3 = st.columns(3)
                with col_act1:
                    if st.button(f"🚫 حظر وحظر حساب {accused}", key=f"ban_act_{t_id}", use_container_width=True):
                        db.collection("banned_users").document(accused).set({
                            "username": accused,
                            "reason": t_data.get('type'),
                            "banned_by": user_role,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.error(f"❌ تم إدراج {accused} في القائمة السوداء السحابية وتم قطع اتصاله!")
                with col_act2:
                    if st.button("⚠️ إرسال إنذار رسمي", key=f"warn_{t_id}", use_container_width=True):
                        st.warning(f"🔔 تم إرسال تحذير نهائي إلى {accused}.")
                with col_act3:
                    if st.button("✅ حل النزاع وإغلاق البلاغ", key=f"res_{t_id}", use_container_width=True):
                        db.collection("support_tickets").document(t_id).update({"resolved": True})
                        st.success("🎯 تم تسوية المشكلة وإغلاق الملف.")
                        st.rerun()
            
            if not has_tickets:
                st.info("🟢 المنصة آمنة ومستقرة بالكامل الآن.")
                if st.button("➕ إنشاء محاكاة بلاغ تجاوز تجريبي للـفحص"):
                    db.collection("support_tickets").add({
                        "reporter_name": "العميل محمد علي",
                        "reporter_role": "عميل",
                        "accused_name": "الكابتن أحمد",
                        "accused_role": "مندوب/سائق",
                        "type": "شبهة احتيال مالي وتجاوز سياسة التسليم الكاش",
                        "details": "المندوب استلم قيمة الطرد واختفى ولم يقم بتحويلها للمحفظة المركزية.",
                        "resolved": False,
                        "timestamp": "2026-05-18"
                    })
                    st.rerun()
        except Exception as e:
            st.error(f"خطأ: {e}")

# --- التبويب الثاني: اعتماد مستندات السائقين والمناديب (المضافة حديثاً) ---
with tab_drivers_kyc:
    st.subheader("🚗 لوحة مراجعة واعتماد مستندات السائقين والمناديب")
    
    if db is not None:
        try:
            drivers_ref = db.collection("users").where("kycStatus", "==", "Pending Review").stream()
            pending_drivers = list(drivers_ref)
            
            if not pending_drivers:
                st.info("🟢 لا توجد طلبات توثيق جديدة معلقة للسائقين في الوقت الحالي.")
            else:
                st.write(f"عدد السائقين في انتظار الاعتماد: **{len(pending_drivers)}**")
                
                for doc in pending_drivers:
                    driver_data = doc.to_dict()
                    phone = doc.id
                    
                    with st.expander(f"👤 السائق: {driver_data.get('fullName', 'غير معروف')} - هاتف: {phone}"):
                        st.write(f"**الرقم القومي:** {driver_data.get('nationalId', 'غير متوفر')}")
                        st.write(f"**رقم الرخصة:** {driver_data.get('licenseNumber', 'غير متوفر')}")
                        st.write(f"**نوع الخدمة:** {driver_data.get('role', 'سائق')}")
                        
                        docs = driver_data.get("documents", {})
                        st.markdown("---")
                        st.write("📄 **المستندات المقدمة:**")
                        st.text(f"رخصة القيادة / البطاقة (أمامي): {docs.get('idFront', 'غير متوفر')}")
                        st.text(f"رخصة القيادة / البطاقة (خلفي): {docs.get('idBack', 'غير متوفر')}")
                        
                        col_k1, col_k2 = st.columns(2)
                        with col_k1:
                            if st.button("✅ موافقة وتفعيل حساب السائق", key=f"approve_driver_{phone}", use_container_width=True):
                                db.collection("users").document(phone).update({
                                    "kycStatus": "Approved",
                                    "updatedAt": firestore.SERVER_TIMESTAMP
                                })
                                st.success(f"تم اعتماد حساب السائق {phone} بنجاح!")
                                st.info("📨 تم إرسال رسالة إلى السائق: 'تم مراجعة البيانات الشخصية وتم تأكيد وتفعيل حسابك بنجاح ويمكنك الأن استقبال الطلبات او الرحلات'.")
                                st.rerun()
                        with col_k2:
                            if st.button("❌ رفض المستندات", key=f"reject_driver_{phone}", use_container_width=True):
                                db.collection("users").document(phone).update({
                                    "kycStatus": "Rejected",
                                    "updatedAt": firestore.SERVER_TIMESTAMP
                                })
                                st.warning(f"تم رفض طلب السائق {phone}.")
                                st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء جلب بيانات السائقين: {e}")

# --- التبويب الثالث: دفتر الحسابات والضرائب ---
with tab_finance:
    st.subheader("📈 التدفقات المالية والضرائب")
    st.caption("يعرض الأرباح والعمولات والضرائب للرحلات المقفلة بدقة.")

# --- التبويب الرابع: الهيكل الإداري ---
with tab_staff:
    st.subheader("👥 هيكل الموظفين والمسؤوليات")
    if user_role == "موظف دعم فني (Support Agent)":
        st.error("⚠️ ليس لديك صلاحية لعرض الهيكل.")
    else:
        st.success(f"🔑 صلاحية ({user_role}) نشطة لإدارة شؤون الموظفين.")

# --- التبويب الخامس: القائمة السوداء (المحظورين) ---
with tab_ban_list:
    st.subheader("🛑 جدول الحسابات المحظورة والمجمدة حالياً")
    if db is not None:
        banned_docs = db.collection("banned_users").stream()
        banned_list = []
        for b in banned_docs:
            b_data = b.to_dict()
            banned_list.append({
                "الحساب المحظور": b_data.get("username"),
                "سبب الحظر": b_data.get("reason"),
                "المسؤول عن الحظر": b_data.get("banned_by")
            })
        if banned_list:
            st.table(banned_list)
            if st.button("🔄 فك حظر الجميع وتصفير القائمة السوداء"):
                for b in db.collection("banned_users").stream():
                    db.collection("banned_users").document(b.id).delete()
                st.success("✅ تم تنظيف القائمة السوداء وإعادة الصلاحية لكافة الحسابات!")
                st.rerun()
        else:
            st.info("🕊️ القائمة بيضاء، لا يوجد أي مستخدم محظور حالياً.")
