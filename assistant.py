import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. الهوية البصرية (الروزماري الفاخر) ---
st.set_page_config(page_title="منصة المنجز V11 - الإطلاق الشامل", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8faf8; }
    .stButton>button { border-radius: 12px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; width: 100%; }
    .order-card { background: white; padding: 20px; border-radius: 15px; border: 1px solid #eee; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .settings-row { display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid #eee; background: white; border-radius: 8px; margin-bottom: 5px; cursor: pointer; }
    .user-card { text-align: center; padding: 15px; background: #ffffff; border-radius: 15px; border: 1px solid #e0e0e0; }
    .status-online { color: #28a745; font-weight: bold; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات والجلسات (V9 + V11) ---
if 'db' not in st.session_state:
    st.session_state['db'] = {"admin": {"pw": "123", "role": "القائد", "name": "أحمد السفير", "phone": "01000000000"}}
if 'orders' not in st.session_state:
    st.session_state['orders'] = [
        {"id": "349180745", "type": "إقرار قيمة مضافة", "details": "نشاط تجاري - يناير", "price": "113.0", "status": "قيد المراجعة", "time": "منذ ساعتين"},
        {"id": "349172626", "type": "فحص نثريات", "details": "مراجعة مصروفات إدارية", "price": "132.0", "status": "تم الاعتماد", "time": "منذ 5 ساعات"}
    ]
if 'chat' not in st.session_state:
    st.session_state['chat'] = [{"u": "🤖 مساعد المنجز", "t": "أهلاً بك! يرجى رفع وثائقك (البطاقة والسجل) لنبدأ العمل فوراً."}]
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 3. محرك الحسابات الضريبية ---
def calculate_tax(amount):
    vat = amount * 0.14
    ins = amount * 0.1875
    comm = amount * 0.30 
    net = amount - (vat + ins + comm)
    return vat, ins, comm, net

# --- 4. بوابة الدخول والتسجيل (بوابة المنجز الأصلية) ---
def login_screen():
    st.title("🌿 بوابة المنجز V11 | الأمان الضريبي بالثانية")
    t1, t2 = st.tabs(["🔑 دخول الموثقين", "📝 إنشاء حساب جديد"])
    
    with t1:
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.button("دخول آمن للنظام"):
            if u in st.session_state['db'] and st.session_state['db'][u]['pw'] == p:
                st.session_state['logged_in'] = True
                st.session_state['user_data'] = st.session_state['db'][u]
                st.rerun()
            else: st.error("بيانات غير صحيحة")
            
    with t2:
        role = st.selectbox("نوع الحساب", ["عميل (صاحب نشاط)", "مستشار ضريبي معتمد"])
        nu = st.text_input("اسم المستخدم الجديد")
        np = st.text_input("كلمة مرور قوية", type="password")
        n_phone = st.text_input("رقم الهاتف المرتبط بالبطاقة")
        if role == "عميل (صاحب نشاط)":
            st.info("📂 التوثيق القانوني مطلوب:")
            st.file_uploader("ارفع صورة البطاقة الضريبية")
            st.file_uploader("ارفع صورة السجل التجاري")
        if st.button("تأكيد التسجيل والتوثيق"):
            r_map = {"عميل (صاحب نشاط)": "العميل", "مستشار ضريبي معتمد": "المستشار"}
            st.session_state['db'][nu] = {"pw": np, "role": r_map[role], "name": nu, "phone": n_phone}
            st.success("تم تسجيل طلبك بنجاح!")

# --- 5. التطبيق الرئيسي (اللوحات الثلاث) ---
def main_app():
    data = st.session_state['user_data']
    role = data['role']
    name = data['name']

    # القائمة الجانبية الاحترافية
    st.sidebar.markdown(f"""
        <div class="user-card">
            <img src="https://ui-avatars.com/api/?name={name}&background=2e7d32&color=fff" style="border-radius: 50%; width: 70px;">
            <h4>{name}</h4>
            <span class="status-online">● متصل الآن</span><br>
            <small>رتبة: {role} موثق</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.write("---")
    menu = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية", "📋 الطلبات والمهام", "💬 غرفة المحادثات", "📅 المناوبات", "⚙️ الإعدادات العامة"])

    # --- القسم 1: الطلبات (بناءً على صورتك) ---
    if menu == "📋 الطلبات والمهام":
        st.header("📋 إدارة العمليات الضريبية")
        for order in st.session_state['orders']:
            st.markdown(f"""
                <div class="order-card">
                    <div style="display:flex; justify-content:space-between; color:#888;">
                        <span>#{order['id']}</span><span>{order['time']}</span>
                    </div>
                    <div style="font-size:18px; font-weight:bold; color:#2e7d32; margin:10px 0;">{order['type']}</div>
                    <div>{order['details']}</div>
                    <hr>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>الأتعاب: {order['price']} ج.م</b>
                        <span style="background:{'#00c853' if order['status']=='تم الاعتماد' else '#ff9800'}; color:white; padding:5px 15px; border-radius:15px;">{order['status']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # --- القسم 2: الإعدادات (بناءً على صورتك) ---
    elif menu == "⚙️ الإعدادات العامة":
        st.header("⚙️ مركز الإعدادات")
        with st.expander("🛠️ إعدادات الملف الشخصي والضريبي", expanded=True):
            st.markdown('<div class="settings-row"><span>📝 تعديل بيانات السجل التجاري</span><span>⬅️</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="settings-row"><span>💳 حساب صرف العمولات (IBAN)</span><span>⬅️</span></div>', unsafe_allow_html=True)
            st.markdown('<div class="settings-row"><span>🔔 تنبيهات الإقرارات (مفعل)</span><span>⚙️</span></div>', unsafe_allow_html=True)

    # --- القسم 3: الشات وبوت الرد ---
    elif menu == "💬 غرفة المحادثات":
        st.header("💬 التواصل الموثق")
        for m in st.session_state['chat']:
            with st.chat_message("assistant" if "🤖" in m['u'] else "user"):
                st.write(f"**{m['u']}:** {m['t']}")
        msg = st.chat_input("اكتب رسالتك...")
        if msg:
            st.session_state['chat'].append({"u": name, "t": msg})
            if role == "العميل":
                st.session_state['chat'].append({"u": "🤖 مساعد المنجز", "t": "رسالتك وصلت للمستشار، جاري الرد في غضون دقائق."})
            st.rerun()

    # --- القسم 4: الرئيسية والمحاسب ---
    elif menu == "🏠 الرئيسية":
        st.title("لوحة التحكم المركزية 🛡️")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("إجمالي الإيرادات المسجلة", "313,319 ج.م")
        with col2:
            st.metric("طلبات اليوم", "5 طلبات")
        
        st.write("---")
        st.subheader("📊 المحاسب السريع (V9)")
        val = st.number_input("أدخل مبلغ العملية:", min_value=0.0)
        if val > 0:
            v, i, c, n = calculate_tax(val)
            st.success(f"صافي الربح بعد الضرائب والعمولات: {n:,.2f} ج.م")

    if st.sidebar.button("🚪 خروج آمن"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- انطلاق النظام ---
if not st.session_state['logged_in']:
    login_screen()
else:
    main_app()
