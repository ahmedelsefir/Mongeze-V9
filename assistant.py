import streamlit as st
import pandas as pd
import time
from datetime import datetime
from honeybadger import honeybadger

# --- 1. إعدادات الهوية والأمان والرادار (Honeybadger) ---
HB_KEY = st.secrets.get("HONEYBADGER_API_KEY", "")

if HB_KEY:
    honeybadger.configure(api_key=HB_KEY)
else:
    st.warning("⚠️ رادار الأخطاء (Honeybadger) غير متصل، يرجى التأكد من المفتاح في Secrets.")

st.set_page_config(page_title="منصة المنجز V34 - نظام الفواتير الذكي", layout="wide", page_icon="🛡️")

# --- بيانات الدخول المعتمدة ---
AUTHORIZED_EMAIL = "ahmedelsefir9@gmail.com"
MASTER_PASSWORD = "hamada 193052" 

# --- 2. التصميم الاحترافي (Emerald & Gold UI) ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3.5em; 
        font-weight: bold; background: #1b5e20; color: white;
        transition: 0.3s; border: none;
    }
    .stButton>button:hover { background: #2e7d32; transform: scale(1.02); }
    .auth-container { 
        background: white; padding: 40px; border-radius: 20px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 10px solid #1b5e20;
    }
    .invoice-box {
        background: white; padding: 40px; border-radius: 15px;
        border: 1px solid #e2e8f0; box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        font-family: 'Cairo', sans-serif; color: #1e293b;
    }
    .plan-card {
        background: #fff; padding: 25px; border-radius: 15px;
        border: 1px solid #e2e8f0; text-align: center;
        transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .plan-card:hover { border-color: #1b5e20; transform: translateY(-5px); }
    h1, h2, h3 { color: #1b5e20; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الجلسة والولوج ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'payment_page' not in st.session_state: st.session_state.payment_page = False
if 'show_invoice' not in st.session_state: st.session_state.show_invoice = False
if 'selected_plan' not in st.session_state: st.session_state.selected_plan = None

if not st.session_state.logged_in:
    st.markdown("<h1>🛡️ المنجز V34: بوابة دخول الإدارة</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        user_email = st.text_input("📨 بريد المدير العام", placeholder="example@gmail.com")
        password_input = st.text_input("🔑 كلمة المرور الخاصة", type="password")
        
        if st.button("🚀 دخول آمن للمنصة"):
            if user_email == AUTHORIZED_EMAIL and password_input == MASTER_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.user_email = user_email
                st.balloons()
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير مطابقة للسجلات المؤمنة.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. واجهة الفاتورة (Invoice) ---
if st.session_state.show_invoice:
    st.title("📄 فاتورة الاشتراك الضريبية")
    
    col_inv1, col_inv2, col_inv3 = st.columns([1, 2, 1])
    with col_inv2:
        st.markdown(f"""
        <div class='invoice-box'>
            <div style='text-align:center;'>
                <h2 style='color:#1b5e20; margin:0;'>إمبراطورية المنجز المحاسبية</h2>
                <p style='color:#64748b;'>رقم الفاتورة: #INV-{int(time.time())}</p>
            </div>
            <hr>
            <table style='width:100%; text-align:right;'>
                <tr><td><b>تاريخ الفاتورة:</b></td><td>{datetime.now().strftime('%Y-%m-%d')}</td></tr>
                <tr><td><b>العميل:</b></td><td>{st.session_state.user_email}</td></tr>
                <tr><td><b>حالة الدفع:</b></td><td><span style='color:green;'>✅ مدفوع</span></td></tr>
            </table>
            <br>
            <table style='width:100%; border-collapse: collapse;'>
                <tr style='background:#f1f8e9;'>
                    <th style='padding:10px; border-bottom:2px solid #1b5e20;'>الوصف</th>
                    <th style='padding:10px; border-bottom:2px solid #1b5e20;'>المبلغ</th>
                </tr>
                <tr>
                    <td style='padding:10px; border-bottom:1px solid #e2e8f0;'>اشتراك {st.session_state.selected_plan}</td>
                    <td style='padding:10px; border-bottom:1px solid #e2e8f0;'>1,500.00 ج.م</td>
                </tr>
                <tr>
                    <td style='padding:10px; font-weight:bold;'>الإجمالي الكلي</td>
                    <td style='padding:10px; font-weight:bold; color:#1b5e20;'>1,500.00 ج.م</td>
                </tr>
            </table>
            <br>
            <p style='font-size:12px; text-align:center; color:#94a3b8;'>شكراً لثقتكم في المنجز. تم إصدار هذه الفاتورة إلكترونياً وهي لا تحتاج لختم.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📥 تحميل الفاتورة (PDF)"):
            st.toast("جاري تحضير ملف الـ PDF...")
        
        if st.button("🏠 العودة للرئيسية"):
            st.session_state.show_invoice = False
            st.rerun()
    st.stop()

# --- 5. واجهة الدفع (Payment) ---
if st.session_state.payment_page:
    st.title("💳 إتمام عملية الاشتراك")
    col_p1, col_p2 = st.columns([1.5, 1])
    
    with col_p1:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.info(f"الخطة المختارة: {st.session_state.selected_plan}")
        card_name = st.text_input("👤 الاسم على البطاقة")
        card_number = st.text_input("💳 رقم البطاقة")
        if st.button("✅ تأكيد الدفع الآن"):
            with st.spinner("جاري التواصل مع بوابة البنك..."):
                time.sleep(2)
                st.session_state.payment_page = False
                st.session_state.show_invoice = True
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🔙 إلغاء"):
        st.session_state.payment_page = False
        st.rerun()
    st.stop()

# --- 6. القائمة الرئيسية ---
st.sidebar.markdown(f"### 👤 القائد: أحمد السفير")
menu = st.sidebar.radio("التحكم:", ["🏠 الرئيسية", "📊 التقارير", "💳 باقات الاشتراك"])

if menu == "🏠 الرئيسية":
    st.title("🌿 مركز القيادة")
    st.success(f"أهلاً بك يا مدير: {st.session_state.user_email}")

elif menu == "💳 باقات الاشتراك":
    st.title("💳 باقات الاشتراك VIP")
    c1, c2, c3 = st.columns(3)
    with c2:
        st.markdown("""<div class='plan-card' style='border-color:#1b5e20; background:#f0f9ff;'>
            <h3 style='color:#1b5e20;'>🥇 الإمبراطور</h3><p>1500 ج.م / شهرياً</p></div>""", unsafe_allow_html=True)
        if st.button("اشترك الآن"):
            st.session_state.selected_plan = "باقة الإمبراطور VIP"
            st.session_state.payment_page = True
            st.rerun()

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()
