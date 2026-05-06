import streamlit as st
from auth import auth_system
from session_manager import session_manager
from config import ROLES

def show_login_page():
    """صفحة تسجيل الدخول الموحدة"""
    
    st.set_page_config(
        page_title="فودي - تسجيل الدخول",
        page_icon="🍔",
        layout="centered"
    )
    
    st.markdown("""
    <style>
        * {
            direction: rtl;
            text-align: right;
        }
        .login-container {
            background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .login-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            font-size: 1.1rem;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">🍔 فودي</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">نظام توصيل الطلبات المتقدم</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # تبويبات التسجيل والدخول
    tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])
    
    # تبويب تسجيل الدخول
    with tab1:
        st.subheader("🔐 تسجيل الدخول")
        
        with st.form("login_form"):
            username = st.text_input(
                "👤 اسم المستخدم",
                placeholder="أدخل اسم المستخدم",
                key="login_username"
            )
            password = st.text_input(
                "🔑 كلمة المرور",
                type="password",
                placeholder="أدخل كلمة المرور",
                key="login_password"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_login = st.form_submit_button("دخول", use_container_width=True)
            with col2:
                st.info("👈 أو أنشئ حساب جديد من اليسار")
            
            if submit_login:
                if not username or not password:
                    st.error("❌ يرجى ملء جميع الحقول")
                else:
                    result = auth_system.login(username, password)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        
        # معلومات حسابات الاختبار
        with st.expander("👉 حسابات اختبار (للتجربة السريعة)"):
            st.markdown("""
            ### 👨‍💼 مسؤول النظام
            - **المستخدم:** admin001
            - **كلمة المرور:** admin123
            
            ### 👨‍💼 موظف
            - **المستخدم:** staff001
            - **كلمة المرور:** staff123
            
            ### 🚗 مندوب توصيل
            - **المستخدم:** driver001
            - **كلمة المرور:** driver123
            
            ### 🍽️ المطعم
            - **المستخدم:** restaurant001
            - **كلمة المرور:** rest123
            
            ### 👤 عميل
            - **المستخدم:** customer001
            - **كلمة المرور:** customer123
            """)
    
    # تبويب إنشاء حساب
    with tab2:
        st.subheader("📝 إنشاء حساب جديد")
        
        with st.form("register_form"):
            username = st.text_input(
                "👤 اسم المستخدم",
                placeholder="اختر اسم مستخدم فريد",
                key="register_username"
            )
            name = st.text_input(
                "👥 الاسم الكامل",
                placeholder="أدخل اسمك الكامل",
                key="register_name"
            )
            email = st.text_input(
                "📧 البريد الإلكتروني",
                placeholder="أدخل بريدك الإلكتروني",
                key="register_email"
            )
            phone = st.text_input(
                "📱 رقم الهاتف",
                placeholder="أدخل رقم الهاتف",
                key="register_phone"
            )
            role = st.selectbox(
                "👨‍💼 اختر دورك",
                options=list(ROLES.keys()),
                format_func=lambda x: ROLES[x]['display_name'],
                key="register_role"
            )
            password = st.text_input(
                "🔑 كلمة المرور",
                type="password",
                placeholder="أدخل كلمة مرور قوية",
                key="register_password"
            )
            password_confirm = st.text_input(
                "🔑 تأكيد كلمة المرور",
                type="password",
                placeholder="أعد إدخال كلمة المرور",
                key="register_password_confirm"
            )
            
            submit_register = st.form_submit_button("إنشاء الحساب", use_container_width=True)
            
            if submit_register:
                # التحقق من البيانات
                if not all([username, name, email, phone, password]):
                    st.error("❌ يرجى ملء جميع الحقول")
                elif password != password_confirm:
                    st.error("❌ كلمات المرور غير متطابقة")
                elif len(password) < 6:
                    st.error("❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                else:
                    result = auth_system.register(username, password, name, role, phone, email)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])

if __name__ == "__main__":
    show_login_page()
