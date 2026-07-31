import hashlib
import time
import streamlit as st
from firebase_admin import firestore

# --- دالة تشفير كلمات السر للأمان ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- شاشة تسجيل الدخول وإنشاء الحساب ---
def show_auth_screen(db):
    st.markdown("""
    <div style='text-align: center; padding: 10px 0;'>
        <h1 style='color: #1E3A8A; margin-bottom: 0;'>🚀 منصة مُنجز</h1>
        <p style='color: #6B7280;'>بوابتك الذكية لخدمات النقل والتوصيل السريع</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])
    
    # -----------------------------------------------------
    # 1️⃣ تبويب تسجيل الدخول
    # -----------------------------------------------------
    with tab_login:
        st.subheader("مرحباً بك مجدداً!")
        phone_input = st.text_input("📱 رقم الهاتف المسجل", key="login_phone")
        pass_input = st.text_input("🔒 كلمة السر", type="password", key="login_pass")
        
        if st.button("🚪 دخول إلى التطبيق", use_container_width=True, type="primary"):
            if not phone_input.strip() or not pass_input.strip():
                st.warning("⚠️ يرجى إدخال رقم الهاتف وكلمة السر.")
            else:
                hashed_pass = hash_password(pass_input.strip())
                
                # الاستعلام من الفايربيز عن المستخدم
                users_ref = db.collection("users")\
                              .where("phone", "==", phone_input.strip())\
                              .where("password", "==", hashed_pass)\
                              .stream()
                
                user_data = None
                user_id = None
                for doc in users_ref:
                    user_data = doc.to_dict()
                    user_id = doc.id
                    break
                
                if user_data:
                    # حفظ بيانات الجلسة
                    st.session_state["is_logged_in"] = True
                    st.session_state["user_id"] = user_id
                    st.session_state["user_data"] = user_data
                    st.session_state["user_role"] = user_data.get("role", "client")
                    
                    st.success(f"✅ مرحباً بك يا {user_data.get('name')}! جاري التوجيه...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ رقم الهاتف أو كلمة السر غير صحيحة. تأكد من البيانات وحاول مجدداً.")

    # -----------------------------------------------------
    # 2️⃣ تبويب إنشاء حساب جديد
    # -----------------------------------------------------
    with tab_register:
        st.subheader("إنشاء حساب جديد في منجز")
        reg_name = st.text_input("👤 الاسم بالكامل", key="reg_name")
        reg_phone = st.text_input("📱 رقم الهاتف (سيستخدم للدخول)", key="reg_phone")
        reg_pass = st.text_input("🔒 كلمة السر الجديدة", type="password", key="reg_pass")
        
        reg_role = st.radio(
            "🎯 نوع الحساب المطلوب:",
            ["عميل (طلب خدمات ومشاوير)", "سائق / كابتن توصيل"],
            horizontal=True
        )
        
        # خيارات إضافية عند اختيار حساب سائق
        vehicle_type = "لا يوجد"
        if "سائق" in reg_role:
            vehicle_type = st.selectbox(
                "🚖 نوع المركبة التي تعمل عليها:",
                ["🚖 تاكسي (مشوار عادي)", "🚘 سيارة ملاكي (توصيل مريح)", "🏍️ موتوسيكل (طرود وسريع)"]
            )

        if st.button("🚀 تسجيل الحساب الآن", use_container_width=True):
            if not reg_name.strip() or not reg_phone.strip() or not reg_pass.strip():
                st.warning("⚠️ يرجى ملء كافة الحقول الأساسية أولاً.")
            else:
                # التحقق من عدم تكرار الحساب بنفس رقم الهاتف
                check_existing = db.collection("users").where("phone", "==", reg_phone.strip()).get()
                if len(check_existing) > 0:
                    st.error("❌ رقم الهاتف هذا مسجل بالفعل لدينا! يرجى استخدام شاشة تسجيل الدخول.")
                else:
                    role_code = "driver" if "سائق" in reg_role else "client"
                    
                    # بناء ملف المستخدم الجديد في الفايربيز
                    new_user = {
                        "name": reg_name.strip(),
                        "phone": reg_phone.strip(),
                        "password": hash_password(reg_pass.strip()),
                        "role": role_code,
                        "vehicle_type": vehicle_type,
                        "wallet_balance": 0.0,
                        "account_status": "active",
                        "created_at": firestore.SERVER_TIMESTAMP
                    }
                    
                    db.collection("users").add(new_user)
                    st.success("🎉 تم إنشاء حسابك بنجاح! يمكنك الآن الانتقال لتبويب 'تسجيل الدخول'.")
