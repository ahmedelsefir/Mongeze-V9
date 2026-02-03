
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="منصة المنجز - الشاملة V15", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stSidebar { background-color: #1e3d23 !important; }
    .welcome-text { color: #2e7d32; font-weight: bold; font-size: 24px; }
    .card { background: white; padding: 15px; border-radius: 10px; border-right: 5px solid #2e7d32; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة قاعدة البيانات اللحظية (Session State) ---
if 'db_shifts' not in st.session_state: st.session_state['db_shifts'] = []
if 'db_orders' not in st.session_state: 
    st.session_state['db_orders'] = [{"id": "349180745", "type": "إقرار ضريبي", "user": "عميل تجريبي", "status": "قيد الانتظار"}]
if 'is_subscribed' not in st.session_state: st.session_state['is_subscribed'] = False
if 'trial_start' not in st.session_state: st.session_state['trial_start'] = datetime.now()

# --- 3. الدوال الذكية (المنطق البرمجي) ---
def check_activation_code(code):
    clean_code = code.replace("-", "").strip()
    return len(clean_code) == 16 and clean_code.isdigit()

def chatbot_response(text):
    text = text.lower()
    if "سجل" in text: return "🤖: السجل التجاري يحتاج لبطاقة ضريبية وعقد إيجار. ارفعهم في 'مركز الوثائق' الآن."
    if "اشتراك" in text: return "🤖: لديك 14 يوم تجربة، بعدها يمكنك التفعيل بكود الـ 16 رقم الخاص بك."
    return "🤖: أهلاً بك في المنجز! أنا هنا لمساعدتك في تنظيم حساباتك."

# --- 4. واجهة الدخول والترحيب الحار ---
if 'logged_in' not in st.session_state:
    st.title("🌿 منصة المنجز - بوابة الدخول الموحدة")
    tab_client, tab_pro = st.tabs(["✨ ترحيب المستخدمين الجدد", "💼 ترحيب المستشارين"])
    
    with tab_client:
        st.markdown("<p class='welcome-text'>🔥 يا أهلاً ببرنس المنجز الجديد!</p>", unsafe_allow_html=True)
        st.info("🎁 هدية القائد: 14 يوم إصدار تجريبي بكامل الصلاحيات مفتوحة لك الآن.")
        if st.button("ابدأ رحلتك المجانية الآن"):
            st.session_state['logged_in'] = True
            st.session_state['role'] = "العميل"
            st.session_state['user_name'] = "عميل جديد"
            st.rerun()

    with tab_pro:
        st.markdown("<p class='welcome-text'>🛡️ أهلاً بأسد المهنة.. المستشار الموثق!</p>", unsafe_allow_html=True)
        st.success("أنت الآن تدخل لبيئة عمل احترافية صممت لتسهيل مهامك الضريبية.")
        name_pro = st.text_input("اسم المستشار")
        if st.button("دخول عرين المنجز"):
            st.session_state['logged_in'] = True
            st.session_state['role'] = "المستشار"
            st.session_state['user_name'] = name_pro
            st.rerun()

# --- 5. التطبيق الرئيسي (بعد الدخول) ---
else:
    role = st.session_state['role']
    name = st.session_state['user_name']
    
    # القائمة الجانبية المرفقة (الخواص كاملة)
    st.sidebar.header(f"🛡️ لوحة {role}")
    st.sidebar.write(f"المستخدم: {name}")
    
    # نظام الاشتراك في السايد بار
    if role == "العميل":
        days_left = 14 - (datetime.now() - st.session_state['trial_start']).days
        if not st.session_state['is_subscribed']:
            if days_left > 0:
                st.sidebar.warning(f"⏳ فترة تجريبية: متبقي {days_left} يوم")
            else:
                st.sidebar.error("❌ انتهت الفترة التجريبية")
            
            st.sidebar.write("---")
            code = st.sidebar.text_input("أدخل كود التفعيل (16 رقم)")
            if st.sidebar.button("تفعيل الاشتراك"):
                if check_activation_code(code):
                    st.session_state['is_subscribed'] = True
                    st.balloons()
                else: st.sidebar.error("الكود غير صحيح")
        else:
            st.sidebar.success("💎 اشتراك VIP مفعل")

    menu = st.sidebar.radio("الخواص والخدمات:", [
        "🏠 اللوحة العامة", "📋 إدارة الطلبات", "📅 جدول المناوبات", 
        "📂 مركز الوثائق", "💬 الشات الذكي", "📊 المحاسب الذكي"
    ])

    # --- التنفيذ الديناميكي للأقسام ---
    if menu == "🏠 اللوحة العامة":
        st.title(f"مرحباً بك في البرنامج المحاسبي (1/5)")
        c1, c2 = st.columns(2)
        with c1: st.metric("الطلبات النشطة", len(st.session_state['db_orders']))
        with c2: st.metric("المستشارين أونلاين", len(st.session_state['db_shifts']))

    elif menu == "📋 إدارة الطلبات":
        st.header("📋 إدارة المهام والطلبات")
        for ord in st.session_state['db_orders']:
            st.markdown(f"<div class='card'><b>طلب {ord['type']}</b><br>الحالة: {ord['status']}</div>", unsafe_allow_html=True)
            if role == "المستشار" and ord['status'] != "تم الاعتماد":
                if st.button(f"اعتماد طلب {ord['id']}"):
                    ord['status'] = "تم الاعتماد"
                    st.rerun()

    elif menu == "📅 جدول المناوبات":
        st.header("📅 تنظيم المناوبات")
        if role == "المستشار":
            day = st.selectbox("اليوم", ["السبت", "الأحد", "الاثنين"])
            shift = st.radio("الفترة", ["صباحي", "مسائي"])
            if st.button("حجز وردية"):
                st.session_state['db_shifts'].append({"المستشار": name, "اليوم": day, "الفترة": shift})
                st.success("تم الحجز!")
        st.table(pd.DataFrame(st.session_state['db_shifts']) if st.session_state['db_shifts'] else "لا يوجد مناوبات")

    elif menu == "📂 مركز الوثائق":
        st.header("📂 رفع البطاقة والسجل")
        st.file_uploader("ارفع صورة البطاقة الضريبية")
        st.file_uploader("ارفع السجل التجاري")
        if st.button("حفظ وربط"): st.success("تم الربط بالبرنامج الحسابي!")

    elif menu == "💬 الشات الذكي":
        st.header("💬 مساعد المنجز")
        if 'chat_p' not in st.session_state: st.session_state['chat_p'] = []
        for m in st.session_state['chat_p']:
            with st.chat_message(m['r']): st.write(m['c'])
        
        p = st.chat_input("اسأل المنجز...")
        if p:
            st.session_state['chat_p'].append({"r": "user", "c": p})
            st.session_state['chat_p'].append({"r": "assistant", "c": chatbot_response(p)})
            st.rerun()

    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state['logged_in'] = False
        st.rerun()
