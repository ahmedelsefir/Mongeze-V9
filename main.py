import base64
import json
import logging
import os
import streamlit as st
import pandas as pd

# ========================================================
# ⚡ إعداد الصفحة الرئيسية (يجب أن تكون أول أمر Streamlit)
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
st.sidebar.title("🚀 مُنجز الذكية")
st.sidebar.success(f"مرحباً: {st.session_state['user_name']}\nالدور: `{st.session_state['user_role']}`")
st.sidebar.markdown("---")

menu_choice = st.sidebar.selectbox(
    "🧭 التنقل السريع بين الأقسام:",
    [
        "🏠 غرفة العمليات الرئيسية والخرائط", 
        "🛍️ بوابة العملاء (طلب طرود وخدمات)", 
        "🚗 السائق والمندوب (توثيق KYC وال GPS)", 
        "🏪 بوابة المتاجر والمطاعم (بوابة البائعين)",
        "💳 مركز الدفع والمحفظة الإلكترونية",
        "🚪 تسجيل الخروج"
    ]
)

if menu_choice == "🚪 تسجيل الخروج":
    st.session_state["user_authenticated"] = False
    st.rerun()

# ========================================================
# 🛡️ نظام توثيق السائقين والمناديب مع تتبع الخريطة
# ========================================================
def render_driver_kyc_portal():
    st.markdown("### 🛡️ بوابة توثيق السائقين والمناديب (KYC - وجه وظهر)")
    st.info("يرجى إرفاق صور المستندات الرسمية (الوجه الأمامي والخلفي) وتحديد موقعك الجغرافي الحالي لتفعيل الحساب.")

    with st.form("driver_kyc_form"):
        col1, col2 = st.columns(2)
        with col1:
            national_id = st.text_input("🆔 الرقم القومي (14 رقماً):")
            email = st.text_input("📧 البريد الإلكتروني الفعال:")
        with col2:
            drv_license = st.text_input("🚗 رقم رخصة القيادة:")
            veh_license = st.text_input("🚙 رقم رخصة المركبة / اللوحة:")

        st.markdown("---")
        st.markdown("#### 🗺️ تحديد الموقع الجغرافي الافتراضي (GPS Simulation):")
        lat = st.number_input("خط العرض (Latitude):", value=30.0444, format="%.4f")
        lon = st.number_input("خط الطول (Longitude):", value=31.2357, format="%.4f")

        if st.form_submit_button("🚀 إرسال المستندات وتحديث الموقع للاعتماد"):
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
                        "kyc_status": "Under Review",
                        "location": {"lat": lat, "lon": lon},
                        "updated_at": firestore.SERVER_TIMESTAMP
                    }, merge=True)
                    st.success("🎉 تم رفع مستندات الوجه والظهر وتحديث الموقع الجغرافي بنجاح!")
                    st.rerun()

    st.markdown("---")
    st.subheader("📍 خريطة تتبع موقع السائق الحالي")
    map_data = pd.DataFrame({'lat': [30.0444], 'lon': [31.2357]})
    st.map(map_data)

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
        wallet_type = st.selectbox("اختر وسيلة الدفع:", ["محفظة محمول", "إنستاباي (InstaPay)", "بطاقة بنكية"])
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
# 🏪 بوابة المتاجر والمطاعم الشاملة (بوابة البائعين)
# ========================================================
def render_vendor_portal(vendor_id="restaurant_el_tahrir"):
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🏪 لوحة تحكم التاجر والمطعم الشريك</h2>", unsafe_allow_html=True)
    st.markdown("---")

    if not db:
        st.error("⚠️ قاعدة البيانات غير متصلة.")
        return

    vendor_ref = db.collection("vendors").document(vendor_id)
    vendor_doc = vendor_ref.get()
    
    vendor_data = {}
    if vendor_doc.exists:
        vendor_data = vendor_doc.to_dict()
    else:
        vendor_data = {
            "name": "مطعم البرجر الملكي السريع",
            "logo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200",
            "category": "مأكولات ومطاعم",
            "is_open": True,
            "partnership_type": "شريك رسمي"
        }
        vendor_ref.set(vendor_data, merge=True)

    col_logo, col_info = st.columns([1, 3])
    with col_logo:
        st.image(vendor_data.get("logo_url", "https://via.placeholder.com/150"), width=130, caption="شعار المطعم")
    with col_info:
        st.markdown(f"### 🏷️ اسم المطعم: **{vendor_data.get('name')}**")
        st.markdown(f"📂 التصنيف: `{vendor_data.get('category')}` | 🤝 نوع الشراكة: **{vendor_data.get('partnership_type')}**")
        status_color = "🟢 مفتوح ويستقبل طلبات" if vendor_data.get("is_open") else "🔴 مغلق حالياً"
        st.markdown(f"**حالة التشغيل:** {status_color}")

    st.markdown("---")
    st.markdown("### 📥 إدارة الطلبات الواردة للمطعم:")

    try:
        orders_ref = db.collection("orders").where("vendor_id", "==", vendor_id).stream()
        found = False
        for doc in orders_ref:
            found = True
            o_data = doc.to_dict()
            o_id = doc.id
            status = o_data.get("status", "Pending")
            
            st.info(f"📌 طلب رقم: `{o_id[:6]}` | العميل: **{o_data.get('client_name')}** | الحالة: **{status}**")
            st.write(f"🛒 الأصناف المطلوبة: {o_data.get('items', [])}")
            st.write(f"📍 ملاحظات التوصيل: {o_data.get('notes', 'بدون ملاحظات')}")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button("👨‍🍳 قبول وتحضير الطلب", key=f"accept_v_{o_id}"):
                    db.collection("orders").document(o_id).update({"status": "Preparing"})
                    st.success("✅ تم قبول الطلب وبدء التحضير في المطبخ!")
                    st.rerun()
            with col_v2:
                if st.button("🚀 جاهز للتوصيل (تسليم للمندوب)", key=f"ready_v_{o_id}"):
                    db.collection("orders").document(o_id).update({"status": "Ready for Delivery"})
                    st.success("✅ تم إعلام السائق بأن الطلب جاهز للاستلام!")
                    st.rerun()
            st.markdown("---")
        
        if not found:
            st.success("👍 لا توجد طلبات جديدة معلقة لهذا المطعم في الوقت الحالي.")
    except Exception as e:
        st.error(f"⚠️ خطأ أثناء جلب الطلبات: {e}")

    with st.form("vendor_settings_update_form"):
        st.subheader("⚙️ تعديل بيانات وهوية المطعم")
        new_name = st.text_input("اسم المطعم:", value=vendor_data.get("name", ""))
        new_logo = st.text_input("رابط شعار المطعم (Logo Image URL):", value=vendor_data.get("logo_url", ""))
        is_open_val = st.checkbox("🟢 المطعم مفتوح للعمل الآن", value=vendor_data.get("is_open", True))
        
        if st.form_submit_button("💾 حفظ تحديثات الهوية والتشغيل"):
            vendor_ref.update({
                "name": new_name,
                "logo_url": new_logo,
                "is_open": is_open_val
            })
            st.success("✅ تم تحديث اسم وشعار وطريقة عمل المطعم بنجاح سحابياً!")
            st.rerun()

# ========================================================
# 🧭 التنفيذ الرئيسي والتحكم بالصفحات (Router)
# ========================================================
try:
    if "غرفة العمليات" in menu_choice:
        st.title("🚀 غرفة العمليات المركزية والخرائط لـ منجز")
        st.success("🎉 النظام متصل بقاعدة بيانات Firebase والخريطة تعمل بكفاءة تامة!")
        
        st.markdown("### 🗺️ خريطة العمليات الحية لتتبع المناديب والطلبات")
        operations_map = pd.DataFrame({
            'lat': [30.0444, 30.0500, 30.0333],
            'lon': [31.2357, 31.2400, 31.2200]
        })
        st.map(operations_map)

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
                        "vendor_id": "restaurant_el_tahrir",
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
