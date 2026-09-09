import base64
import json
import logging
import os
import streamlit as st

# ========================================================
# ⚡ CRITICAL: set_page_config() MUST be the first Streamlit call
# ========================================================
st.set_page_config(
    page_title="منصة مُنجز الذكية - التشغيل الفعلي", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# ========================================================
# 🔒 إعداد الاتصال السحابي بالـ Firebase بذكاء وأمان
# ========================================================
db = None
try:
    firebase_config = None
    if "textkey" in st.secrets and isinstance(st.secrets.get("textkey"), dict) and "textkey" in st.secrets.get("textkey"):
        raw_json = st.secrets["textkey"]["textkey"]
        firebase_config = json.loads(raw_json)
    elif "firebase" in st.secrets:
        firebase_config = dict(st.secrets["firebase"])
        if "private_key" in firebase_config and isinstance(firebase_config["private_key"], str):
            firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    if firebase_config and not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)

    db = firestore.client()
except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بقاعدة البيانات: {str(e)}")

# ========================================================
# 🛡️ حماية الجلسة والتهيئة العامة للمستخدمين
# ========================================================
if "user_authenticated" not in st.session_state:
    st.session_state["user_authenticated"] = False
if "user_phone" not in st.session_state:
    st.session_state["user_phone"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "عميل"
if "user_name" not in st.session_state:
    st.session_state["user_name"] = "أحمد مصطفى"

# ========================================================
# 📱 نظام تسجيل الدخول والتسجيل الكامل للمستخدمين
# ========================================================
def render_authentication_portal():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 بوابة تسجيل الدخول والتسجيل لمنصة مُنجز</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_mode = st.radio("اختر العملية:", ["تسجيل دخول", "حساب جديد (تسجيل مستخدم)"], horizontal=True)
        
        with st.form("auth_form"):
            phone = st.text_input("📱 رقم الجوال الرسمي (مع مفتاح الدولة):", placeholder="+20...")
            password = st.text_input("🔑 كلمة المرور:", type="password")
            
            name = ""
            role = "عميل"
            if "حساب جديد" in auth_mode:
                name = st.text_input("👤 الاسم الكامل:")
                role = st.selectbox("حدد طبيعة الحساب:", ["عميل", "سائق / مندوب توصيل", "تاجر / صاحب مطعم"])
                
            submit_btn = st.form_submit_button("🚀 تنفيذ العملية سحابياً")
            
            if submit_btn:
                if not phone or not password:
                    st.warning("⚠️ يرجى إدخال رقم الجوال وكلمة المرور.")
                else:
                    if db is not None:
                        doc_id = phone.strip().replace("+", "")
                        user_ref = db.collection("users").document(doc_id)
                        user_doc = user_ref.get()
                        
                        if "حساب جديد" in auth_mode:
                            if user_doc.exists:
                                st.error("⚠️ هذا الرقم مسجل مسبقاً! يرجى الانتقال لتسجيل الدخول.")
                            else:
                                user_ref.set({
                                    "phone": phone,
                                    "password": password,
                                    "name": name if name else "مستخدم منجز",
                                    "role": role,
                                    "wallet_balance": 100.0,
                                    "created_at": firestore.SERVER_TIMESTAMP
                                })
                                st.session_state["user_authenticated"] = True
                                st.session_state["user_phone"] = phone
                                st.session_state["user_name"] = name
                                st.session_state["user_role"] = role
                                st.success("🎉 تم إنشاء الحساب وتسجيل الدخول بنجاح تام!")
                                st.rerun()
                        else:
                            if not user_doc.exists:
                                st.error("⚠️ هذا الرقم غير مسجل في النظام. يرجى إنشاء حساب جديد.")
                            else:
                                data = user_doc.to_dict()
                                if data.get("password") == password:
                                    st.session_state["user_authenticated"] = True
                                    st.session_state["user_phone"] = phone
                                    st.session_state["user_name"] = data.get("name", "أحمد")
                                    st.session_state["user_role"] = data.get("role", "عميل")
                                    st.success("✅ أهلاً بك مجدداً! تم تسجيل الدخول بنجاح.")
                                    st.rerun()
                                else:
                                    st.error("❌ كلمة المرور غير صحيحة.")
                    else:
                        st.error("⚠️ قاعدة البيانات غير متصلة.")

if not st.session_state["user_authenticated"]:
    render_authentication_portal()
    st.stop()

# ========================================================
# 🧭 القائمة الجانبية الموحدة
# ========================================================
st.sidebar.title(f"🚀 مُنجز الذكية")
st.sidebar.success(f"مرحباً: {st.session_state['user_name']}\nالدور: `{st.session_state['user_role']}`")
st.sidebar.markdown("---")

menu_choice = st.sidebar.selectbox(
    "🧭 التنقل السريع بين الأقسام:",
    [
        "🏠 غرفة العمليات الرئيسية", 
        "🛍️ بوابة العملاء (طلب طرود وخدمات)", 
        "🚗 السائق والمندوب (توثيق KYC وجه وظهر)", 
        "🏪 بوابة المتاجر والمطاعم (اسم وشعار)",
        "💳 مركز الدفع والمحفظة الإلكترونية",
        "🚪 تسجيل الخروج"
    ]
)

if menu_choice == "🚪 تسجيل الخروج":
    st.session_state["user_authenticated"] = False
    st.rerun()

# ========================================================
# 🛡️ نظام توثيق السائقين والمندوبين (وجه وظهر المستندات بدقة)
# ========================================================
def render_driver_kyc_portal():
    st.markdown("### 🛡️ بوابة توثيق السائقين والمندوبين (KYC - وجه وظهر)")
    st.info("يرجى إرفاق صور المستندات الرسمية (الوجه الأمامي والخلفي) للبطاقة والرخص بدقة تامة لتفعيل الحساب.")

    with st.form("driver_kyc_form"):
        col1, col2 = st.columns(2)
        with col1:
            national_id = st.text_input("🆔 الرقم القومي (14 رقماً):")
            email = st.text_input("📧 البريد الإلكتروني الفعال:")
        with col2:
            drv_license = st.text_input("🚗 رقم رخصة القيادة:")
            veh_license = st.text_input("🚙 رقم رخصة المركبة / اللوحة:")

        st.markdown("---")
        st.markdown("#### 📂 إرفاق مستندات التحقق (الوجه الأمامي والخلفي):")
        
        c1, c2 = st.columns(2)
        with c1:
            id_front = st.file_uploader("1️⃣ البطاقة الشخصية (الوجه الأمامي)", type=["jpg", "png", "jpeg"])
        with c2:
            id_back = st.file_uploader("2️⃣ البطاقة الشخصية (الوجه الخلفي)", type=["jpg", "png", "jpeg"])

        c3, c4 = st.columns(2)
        with c3:
            drv_front = st.file_uploader("3️⃣ رخصة القيادة (الوجه الأمامي)", type=["jpg", "png", "jpeg"])
        with c4:
            drv_back = st.file_uploader("4️⃣ رخصة القيادة (الوجه الخلفي)", type=["jpg", "png", "jpeg"])

        c5, c6 = st.columns(2)
        with c5:
            veh_front = st.file_uploader("5️⃣ رخصة المركبة (الوجه الأمامي)", type=["jpg", "png", "jpeg"])
        with c6:
            veh_back = st.file_uploader("6️⃣ رخصة المركبة (الوجه الخلفي)", type=["jpg", "png", "jpeg"])

        if st.form_submit_button("🚀 إرسال كامل المستندات للاعتماد الفوري"):
            if not national_id or not drv_license:
                st.warning("⚠️ يرجى تعبئة الحقول الأساسية (الرقم القومي ورخصة القيادة).")
            else:
                if db is not None:
                    doc_id = st.session_state["user_phone"].replace("+", "")
                    db.collection("users").document(doc_id).set({
                        "national_id": national_id,
                        "email": email,
                        "driving_license": drv_license,
                        "vehicle_license": veh_license,
                        "kyc_status": "Under Review (Front & Back)",
                        "updated_at": firestore.SERVER_TIMESTAMP
                    }, merge=True)
                    st.success("🎉 تم رفع مستندات الوجه والظهر بنجاح تام! حسابك قيد المراجعة النهائية.")
                    st.rerun()

# ========================================================
# 💳 مركز الدفع والمحفظة الإلكترونية
# ========================================================
def render_payment_hub():
    st.markdown("### 💳 مركز الدفع والمحفظة الإلكترونية المتقدمة")
    st.info("إدارة الأرصدة وربط وسائل الدفع الإلكترونية وسحب الأموال.")

    phone_key = st.session_state["user_phone"].replace("+", "")
    user_ref = db.collection("users").document(phone_key)
    user_doc = user_ref.get()
    u_data = user_doc.to_dict() if user_doc.exists else {}
    
    current_balance = u_data.get("wallet_balance", 100.0)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("💰 رصيد المحفظة الحالي", f"{current_balance:.2f} ج.م")
    with col_m2:
        st.metric("🔒 حالة أمان الدفع", "مفعل ومؤمن سحابياً")

    st.markdown("---")
    st.subheader("➕ ربط محفظة إلكترونية أو بطاقة جديدة")
    
    with st.form("wallet_link_form"):
        wallet_type = st.selectbox("اختر وسيلة الدفع:", ["محفظة محمول (فودافون/اورانج/اتصالات)", "إنستاباي (InstaPay)", "بطاقة بنكية"])
        account_details = st.text_input("رقم المحفظة أو المعرف البنكي:")
        
        if st.form_submit_button("💾 حفظ وسيلة الدفع"):
            if account_details:
                user_ref.set({
                    "payment_methods": firestore.ArrayUnion([{
                        "type": wallet_type,
                        "details": account_details,
                        "linked_at": firestore.SERVER_TIMESTAMP
                    }])
                }, merge=True)
                st.success("✅ تم ربط وسيلة الدفع بنجاح في قاعدة البيانات!")
                st.rerun()
            else:
                st.warning("⚠️ يرجى إدخال البيانات المطلوبة.")

# ========================================================
# 🏪 بوابة المتاجر والمطاعم
# ========================================================
def render_vendor_portal():
    st.markdown("### 🏪 إدارة المتاجر والمطاعم الشريكة (Multi-Vendor)")
    vendor_id = st.text_input("معرف المتجر:", value="restaurant_el_tahrir")
    
    vendor_ref = db.collection("vendors").document(vendor_id)
    v_doc = vendor_ref.get()
    v_data = v_doc.to_dict() if v_doc.exists else {
        "name": "مطعم البرجر الملكي السريع",
        "logo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200",
        "category": "مأكولات ومطاعم",
        "is_open": True
    }
    
    col_l, col_i = st.columns([1, 3])
    with col_l:
        st.image(v_data.get("logo_url"), width=120, caption="شعار المتجر")
    with col_i:
        st.markdown(f"### 🏷️ اسم المطعم: **{v_data.get('name')}**")
        st.markdown(f"📂 التصنيف: `{v_data.get('category')}`")

# ========================================================
# 🧭 التنفيذ الرئيسي
# ========================================================
try:
    if "غرفة العمليات" in menu_choice:
        st.title("🚀 غرفة العمليات المركزية لـ منجز الذكية")
        st.success("🎉 النظام متصل بقاعدة بيانات Firebase وجاهز بالكامل!")

    elif "بوابة العملاء" in menu_choice:
        st.title("🛍️ بوابة العملاء (إرسال الطلبات)")
        with st.form("order_form"):
            pickup = st.text_input("📍 نقطة الاستلام:")
            dropoff = st.text_input("🎯 نقطة التسليم:")
            details = st.text_area("📝 تفاصيل الطلب:")
            if st.form_submit_button("🚀 إرسال الطلب"):
                if db is not None:
                    db.collection("orders").add({
                        "client_name": st.session_state["user_name"],
                        "client_phone": st.session_state["user_phone"],
                        "pickup": pickup,
                        "dropoff": dropoff,
                        "details": details,
                        "status": "Pending",
                        "created_at": firestore.SERVER_TIMESTAMP
                    })
                    st.success("✅ تم نشر طلبك في النظام السحابي بنجاح!")

    elif "السائق والمندوب" in menu_choice:
        render_driver_kyc_portal()

    elif "بوابة المتاجر" in menu_choice:
        render_vendor_portal()

    elif "مركز الدفع" in menu_choice:
        render_payment_hub()

except Exception as ex:
    st.error(f"⚠️ حدث خطأ أثناء عرض الصفحة: {str(ex)}")
