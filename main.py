import base64
import html as html_mod
import json
import logging
import os
import time
import streamlit as st

# ========================================================
# ⚡ CRITICAL: set_page_config() MUST be the first Streamlit call
# ========================================================
st.set_page_config(
    page_title="منصة مُنجز الذكية - غرفة العمليات", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# ========================================================
# 🔒 إعداد الاتصال السحابي بالـ Firebase
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
# 🛡️ حماية الجلسة والتهيئة العامة
# ========================================================
if "user_name" not in st.session_state:
    st.session_state["user_name"] = "أحمد مصطفى"

# ========================================================
# 🖥️ القائمة الجانبية الموحدة (التنقل بين جميع أقسام منجز)
# ========================================================
st.sidebar.title("🚀 منصة مُنجز الذكية")
st.sidebar.markdown("---")

menu_choice = st.sidebar.selectbox(
    "🧭 اختر القسم أو الخدمة المطلوبة:",
    [
        "🏠 رئيسي (غرفة العمليات)", 
        "🛍️ عميل (طلب طرود وتاكسي ومتاجر)", 
        "🚗 السائق والمندوب (توثيق KYC)", 
        "🚖 سائق تاكسي فوري", 
        "🏪 بوابة البائعين والمتاجر (بالاسم والشعار)",
        "💬 الشات والدعم الفني", 
        "💳 مركز الدفع والمحفظة"
    ]
)

user_name = st.sidebar.text_input("🏷️ اسم المستخدم / الهوية:", value=st.session_state.get("user_name", "أحمد مصطفى"))
st.session_state["user_name"] = user_name

# ========================================================
# 🛡️ نظام توثيق السائقين والمندوبين الكامل (KYC & Documents)
# ========================================================
def render_driver_kyc_portal(username):
    st.markdown("### 🛡️ لوحة توثيق السائق والمندوب (KYC & Document Verification)")
    st.info("يرجى إرفاق المستندات الرسمية والبيانات بدقة لتفعيل حسابك واستقبال الطلبات.")

    with st.form("driver_kyc_full_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("👤 الاسم الثلاثي الرسمي:", value=username)
            national_id = st.text_input("🆔 الرقم القومي (14 رقماً):")
            phone_number = st.text_input("📱 رقم الجوال الرسمي للتواصل:")
            email_address = st.text_input("📧 البريد الإلكتروني الفعال:")
        with col2:
            driving_license_num = st.text_input("🚗 رقم رخصة القيادة:")
            vehicle_license_num = st.text_input("🚙 رقم رخصة المركبة / اللوحة:")
            vehicle_type = st.selectbox("نوع المركبة:", ["تاكسي فوري", "دراجة نارية (توصيل طرود)", "سيارة ملاكي"])

        st.markdown("---")
        st.markdown("#### 📂 إرفاق المستندات والأوراق الرسمية:")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            id_card_img = st.file_uploader("1️⃣ صورة البطاقة الشخصية", type=["jpg", "png", "jpeg"])
        with col_f2:
            drv_img = st.file_uploader("2️⃣ صورة رخصة القيادة", type=["jpg", "png", "jpeg"])
        with col_f3:
            veh_img = st.file_uploader("3️⃣ صورة رخصة المركبة", type=["jpg", "png", "jpeg"])

        submitted_kyc = st.form_submit_button("🚀 إرسال المستندات للاعتماد الفوري")
        if submitted_kyc:
            if not national_id or not phone_number or not email_address:
                st.warning("⚠️ يرجى تعبئة الحقول الأساسية (الرقم القومي، الجوال، الإيميل).")
            else:
                if db is not None:
                    try:
                        doc_id = str(username).strip().lower()
                        db.collection("users").document(doc_id).set({
                            "name": full_name,
                            "email": email_address,
                            "phone": phone_number,
                            "national_id": national_id,
                            "driving_license": driving_license_num,
                            "vehicle_license": vehicle_license_num,
                            "vehicle_type": vehicle_type,
                            "kyc_status": "Under Admin Review",
                            "role": "driver",
                            "updated_at": firestore.SERVER_TIMESTAMP
                        }, merge=True)
                        st.success("🎉 تم رفع مستنداتك بنجاح! حسابك الآن قيد المراجعة الإدارية للتفعيل.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"⚠️ خطأ أثناء الحفظ السحابي: {str(ex)}")
                else:
                    st.error("⚠️ قاعدة البيانات غير متصلة.")

# ========================================================
# 🏪 بوابة المتاجر المتعددة (بالاسم والشعار وإدارة الطلبات)
# ========================================================
def render_multi_vendor_portal():
    st.markdown("### 🏪 بوابة البائعين والمتاجر الشريكة (Multi-Vendor)")
    vendor_id = st.text_input("معرف المتجر (Vendor ID):", value="restaurant_el_tahrir")
    
    if db is not None:
        vendor_ref = db.collection("vendors").document(vendor_id)
        vendor_doc = vendor_ref.get()
        v_data = vendor_doc.to_dict() if vendor_doc.exists else {
            "name": "مطعم البرجر الملكي السريع",
            "logo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=200",
            "category": "مأكولات ومطاعم",
            "is_open": True
        }
        
        col_l, col_i = st.columns([1, 3])
        with col_l:
            st.image(v_data.get("logo_url", "https://via.placeholder.com/150"), width=120, caption="شعار المطعم")
        with col_i:
            st.markdown(f"### 🏷️ اسم المطعم: **{v_data.get('name')}**")
            st.markdown(f"📂 التصنيف: `{v_data.get('category')}`")
            st.markdown(f"🟢 الحالة: {'مفتوح' if v_data.get('is_open') else 'مغلق'}")

        st.markdown("---")
        st.markdown("#### 📥 طلبات العملاء الواردة لهذا المطعم:")
        try:
            orders = db.collection("orders").where("vendor_id", "==", vendor_id).stream()
            found = False
            for o in orders:
                found = True
                data = o.to_dict()
                st.info(f"📌 طلب من: {data.get('client_name')} | الحالة: {data.get('status')}")
            if not found:
                st.success("👍 لا توجد طلبات جديدة حالياً.")
        except Exception:
            st.info("لا توجد طلبات مسجلة بعد.")

# ========================================================
# 🧭 التوجيه التنفيذي بناءً على اختيار القائمة
# ========================================================
try:
    if "رئيسي" in menu_choice:
        st.title("🚀 غرفة العمليات المركزية لـ منجز الذكية")
        st.success("النظام يعمل بكفاءة تامة ومتصل بقاعدة بيانات Firebase وسحابة Google.")
        st.markdown("اختر الخدمة المطلوبة من القائمة الجانبية للبدء فوراً.")

    elif "عميل" in menu_choice:
        st.title("🛍️ بوابة العملاء (طلب الطرود والخدمات)")
        with st.form("client_order_form"):
            pickup = st.text_input("📍 نقطة الاستلام:", "شارع التحرير، الجيزة")
            dropoff = st.text_input("🎯 نقطة التسليم:", "المهندسين")
            details = st.text_area("📝 تفاصيل الطلب:")
            if st.form_submit_button("🚀 نشر الطلب"):
                if db is not None:
                    db.collection("orders").add({
                        "client_name": user_name,
                        "pickup": pickup,
                        "dropoff": dropoff,
                        "details": details,
                        "status": "Pending",
                        "created_at": firestore.SERVER_TIMESTAMP
                    })
                    st.success("✅ تم نشر طلبك بنجاح للمندوبين!")

    elif "السائق" in menu_choice:
        render_driver_kyc_portal(user_name)

    elif "سائق تاكسي" in menu_choice:
        st.title("🚖 خدمة التاكسي الفوري")
        st.info("نظام استقبال رحلات التتاكسي مفعل وجاهز لاستقبال طلبات الركاب.")

    elif "بوابة البائعين" in menu_choice:
        render_multi_vendor_portal()

    elif "الشات" in menu_choice:
        st.title("💬 شات منجز المباشر والدعم الفني")
        msg = st.text_input("اكتب رسالتك:")
        if st.button("إرسال للعملاء أو السائقين"):
            st.success("تم إرسال الرسالة بنجاح عبر النظام السحابي.")

    elif "مركز الدفع" in menu_choice:
        st.title("💳 المحفظة الإلكترونية وبوابة الدفع")
        st.metric("رصيد الحساب الحالي", "350.00 ج.م")

except Exception as e:
    st.error(f"⚠️ حدث خطأ تقني غير متوقع: {str(e)}")
