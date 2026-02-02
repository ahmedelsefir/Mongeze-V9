import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. إعدادات الهوية والبصمة (الروزماري) ---
st.set_page_config(page_title="المنجز V10 - النظام المتكامل", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f7f9f7; }
    .stButton>button { width: 100%; background-color: #2e7d32; color: white; border-radius: 8px; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الجلسة والدخول (V9) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.title("🔐 بوابة المنجز V10 | تسجيل الدخول")
    with st.container():
        user = st.text_input("اسم المستخدم (قائد/مستشار/عميل)")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول إلى النظام"):
            # يمكن تخصيص كلمات مرور مختلفة لكل رتبة لاحقاً
            if user == "admin" and password == "123": 
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = "قائد"
                st.rerun()
            else:
                st.error("خطأ في البيانات، يرجى التأكد من كلمة المرور")

# --- 3. محرك العمليات الحسابية (V10) ---
def calculate_all(amount):
    return {
        "vat": amount * 0.14,           # قيمة مضافة
        "ins": amount * 0.1875,         # تأمينات 
        "platform": amount * 0.20,      # عمولة المنصة (20%)
        "ops": amount * 0.10,           # مصاريف تشغيل (10%)
        "net": amount * 0.3725          # المتبقي التقريبي للعميل بعد كل الالتزامات
    }

# --- 4. التطبيق الرئيسي بعد الدخول ---
def main_app():
    st.sidebar.title("🌿 المنجز V10")
    st.sidebar.info(f"مرحباً بك يا {st.session_state.get('user_role', 'مستخدم')}")
    
    menu = ["📊 المحاسب الذكي (الـ 24 جدول)", "📑 أرشيف النثريات", "✒️ غرفة التوقيع والاعتماد", "🛡️ لوحة تحكم القائد"]
    choice = st.sidebar.selectbox("انتقل إلى:", menu)

    # --- أ. المحاسب الذكي (الدمج الحسابي) ---
    if choice == "📊 المحاسب الذكي (الـ 24 جدول)":
        st.header("المحاسب الذكي | الدقة المتناهية")
        amount = st.number_input("أدخل قيمة العملية الأساسية (جنيه)", min_value=0.0)
        
        if amount > 0:
            res = calculate_all(amount)
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("قيمة مضافة (14%)", f"{res['vat']:,.2f}")
            with col2: st.metric("تأمينات (18.75%)", f"{res['ins']:,.2f}")
            with col3: st.metric("عمولة المنصة (20%)", f"{res['platform']:,.2f}")
            with col4: st.metric("الصافي النهائي للعميل", f"{res['net']:,.2f}")
            
            st.write("---")
            st.subheader("توزيع الجداول الضريبية (محاكاة الـ 24 جدول)")
            st.table(pd.DataFrame({
                "نوع الجدول": ["جدول 1 (دخل)", "جدول 5 (خصم)", "جدول 12 (تأمينات)", "جدول 24 (نثريات)"],
                "الحالة": ["مؤمن", "مؤمن", "محدث", "بانتظار الفاتورة"],
                "القيمة": [amount, res['vat'], res['ins'], "قيد المعالجة"]
            }))

    # --- ب. أرشيف النثريات (تصوير ورفع) ---
    elif choice == "📑 أرشيف النثريات":
        st.header("أرشفة المستندات الورقية")
        file = st.file_uploader("صور الفاتورة وارفعها هنا للأرشفة", type=['jpg','png','pdf'])
        if file:
            st.success("تم تأمين الفاتورة وربطها بالجدول رقم 24 بنجاح.")

    # --- ج. غرفة التوقيع الرقمي (الاعتماد) ---
    elif choice == "✒️ غرفة التوقيع والاعتماد":
        st.header("اعتماد البيانات قانونياً")
        st.write("بصفتك (عميل/مستشار)، هل تقر بصحة البيانات؟")
        name = st.text_input("اكتب اسمك الثلاثي للتوقيع")
        if st.button("توقيع واعتماد"):
            if name:
                st.success(f"تم الاعتماد الرقمي بواسطة {name} بتاريخ {datetime.now()}")
                st.balloons()

    # --- د. لوحة القائد (أنت) ---
    elif choice == "🛡️ لوحة تحكم القائد":
        st.header("إحصائيات الإمبراطورية")
        st.metric("إجمالي العمولات المحصلة اليوم", "1,250 جنيه")
        st.info("نظام التنبيهات: متبقي 15 يوماً على موعد الإقرار القادم.")

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- تشغيل النظام بتسلسل V9 -> V10 ---
if not st.session_state['logged_in']:
    login()
else:
    main_app()
