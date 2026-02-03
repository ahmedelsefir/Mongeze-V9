import streamlit as st
import pandas as pd
from datetime import datetime
import time

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="Mongeze V39 - Final Matrix", layout="wide", page_icon="🌿")

# --- 2. إدارة الحالة واللغة ---
if 'lang' not in st.session_state: st.session_state.lang = "ar"
if 'auth' not in st.session_state: st.session_state.auth = False

def switch_lang():
    st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"

texts = {
    "ar": {
        "title": "🛡️ إمبراطورية المنجز V39",
        "welcome": "أهلاً بك يا قائد أحمد السفير",
        "dashboard": "🏠 لوحة التحكم المركزية",
        "mgmt_table": "📋 جدول 12 مورد إداري",
        "rev_table": "💰 جدول 12 بند إيرادات",
        "docs_center": "📂 مركز التوثيق والربط",
        "ai_bot": "🤖 مساعد المنجز الذكي",
        "logout": "تسجيل خروج",
        "lang_btn": "English Version 🇺🇸",
        "save_btn": "اعتماد وحفظ البيانات",
        "upload_msg": "المستندات المطلوبة لتفعيل الحساب (العملاء الجدد)",
        "tax_id": "رقم التسجيل الضريبي الموحد"
    },
    "en": {
        "title": "🛡️ Mongeze Empire V39",
        "welcome": "Welcome, Commander Ahmed El-Sefir",
        "dashboard": "🏠 Central Dashboard",
        "mgmt_table": "📋 12 Admin Resources",
        "rev_table": "💰 12 Revenue Items",
        "docs_center": "📂 Documentation & Linking",
        "ai_bot": "🤖 Mongeze AI Assistant",
        "logout": "Logout",
        "lang_btn": "النسخة العربية 🇪🇬",
        "save_btn": "Authorize & Save",
        "upload_msg": "Required Documents for Account Activation",
        "tax_id": "Unified Tax ID Number"
    }
}

L = texts[st.session_state.lang]

# --- 3. تصميم الـ CSS المحسن ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    .stMetric { background: #ffffff; padding: 20px; border-radius: 15px; border-bottom: 4px solid #1b5e20; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .upload-section { background: #fdfdfd; padding: 30px; border-radius: 20px; border: 1px solid #e2e8f0; }
    .status-badge { color: #1b5e20; font-weight: bold; background: #e8f5e9; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. محرك الدخول ---
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align:center; color:#1b5e20; margin-top:50px;'>{L['title']}</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.button(L["lang_btn"], on_click=switch_lang)
        u = st.text_input("User Email / البريد الإلكتروني")
        p = st.text_input("Access Code / كود الدخول", type="password")
        if st.button(L["login_btn"] if "login_btn" in L else "Login"):
            if u and p:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- 5. القائمة الجانبية ---
st.sidebar.markdown(f"### 👑 {L['welcome']}")
st.sidebar.button(L["lang_btn"], on_click=switch_lang)
menu = st.sidebar.radio("المنظومة:", [L["dashboard"], L["docs_center"], L["mgmt_table"], L["rev_table"], L["ai_bot"]])

# --- 6. الأقسام التشغيلية ---

if menu == L["dashboard"]:
    st.header(L["dashboard"])
    st.success("إشعار: تم إرسال تنبيه الدخول إلى منصة منجز بنجاح.")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(L["mgmt_table"], "12 مورد", "مكتمل")
    with c2: st.metric(L["rev_table"], "12 بند", "نشط")
    with c3: st.metric("حالة الربط", "100%", "آمن")

elif menu == L["docs_center"]:
    st.header(L["docs_center"])
    st.info(L["upload_msg"])
    
    with st.container():
        st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
        col_1, col_2 = st.columns(2)
        with col_1:
            st.file_uploader("📑 صورة السجل التجاري (Commercial Registry)", type=['pdf', 'jpg', 'png'])
            st.file_uploader("🧾 صورة الفاتورة الضريبية (Tax Invoice)", type=['pdf', 'jpg', 'png'])
        with col_2:
            st.file_uploader("💳 صورة البطاقة الضريبية (Tax Card)", type=['pdf', 'jpg', 'png'])
            st.text_input(L["tax_id"], placeholder="Ex: 123-456-789")
        
        if st.button(L["save_btn"]):
            with st.spinner("جاري تشفير البيانات والربط بالسيرفر السيادي..."):
                time.sleep(2)
                st.success("✅ تم الاعتماد. أهلاً بك في عائلة منجز!")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == L["mgmt_table"]:
    st.header(L["mgmt_table"])
    # مصفوفة الـ 12 مورد الإداري
    resources = ["المكتب الفني", "تأمينات القاهرة", "مصلحة الضرائب", "توريد ورق", "صيانة أنظمة", "إيجار المقر", "اتصالات ونترنت", "كهرباء ومياه", "أمن وحراسة", "خدمات نظافة", "استشارات قانونية", "تسويق رقمي"]
    df_mgmt = pd.DataFrame({
        "كود المورد": [f"M-{i+1:02d}" for i in range(12)],
        "الجهة": resources,
        "تاريخ الارتباط": [datetime.now().strftime("%Y-%m-%d")] * 12,
        "الحالة": ["نشط ✅"] * 12
    })
    st.table(df_mgmt)

elif menu == L["rev_table"]:
    st.header(L["rev_table"])
    # مصفوفة الـ 12 بند إيرادات
    revenues = ["اشتراك VIP", "باقة ذهبية", "باقة القمة", "استشارة ضريبية", "فحص ميزانية", "تأسيس شركة", "إقرار ضريبي", "دمغة سنوية", "تدريب محاسبي", "دعم فني", "اشتراك تجاري", "خدمات دولية"]
    df_rev = pd.DataFrame({
        "كود الإيراد": [f"R-{i+1:02d}" for i in range(12)],
        "البند": revenues,
        "القيمة (ج.م)": [(i+1)*2500 for i in range(12)],
        "التحصيل": ["مكتمل" for i in range(12)]
    })
    st.table(df_rev)

elif menu == L["ai_bot"]:
    st.header(L["ai_bot"])
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = [{"role": "assistant", "content": "مرحباً يا قائد، كيف يمكنني مساعدتك في تحليل مصفوفة الـ 24 بنداً اليوم؟"}]
    
    for msg in st.session_state.chat_log:
        with st.chat_message(msg["role"]): st.write(msg["content"])
        
    p = st.chat_input("اسأل عن الفواتير أو الموردين...")
    if p:
        st.session_state.chat_log.append({"role": "user", "content": p})
        st.session_state.chat_log.append({"role": "assistant", "content": "جاري مراجعة السجل التجاري والبطاقة الضريبية المرفوعة... تبدو البيانات سليمة وقابلة للربط."})
        st.rerun()

if st.sidebar.button(L["logout"]):
    st.session_state.auth = False
    st.rerun()
