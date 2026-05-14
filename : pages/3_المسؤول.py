import streamlit as st
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة (تصميم عريض لاستيعاب البيانات المالية)
st.set_page_config(
    page_title="منجز - لوحة التحكم والمركز المالي",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. الثوابت المحاسبية (يمكنك تعديلها من هنا)
VAT_RATE = 0.14       # ضريبة القيمة المضافة 14%
APP_COMMISSION = 0.10  # عمولة التطبيق 10%

# 3. تنسيق CSS مخصص للواجهة
st.markdown("""
<style>
    .reportview-container .main .block-container { direction: rtl; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
    div[data-testid="stExpander"] { border: 1px solid #FF6B35; border-radius: 10px; }
    h1, h2, h3 { color: #2C3E50; text-align: right; }
</style>
""", unsafe_allow_html=True)

# 4. القائمة الجانبية للتنقل
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🎯 نظام منجز الإداري</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio(
        "اختر القسم:",
        ["📊 لوحة المعلومات العامة", "💰 المركز المالي والضرائب", "🚚 تتبع وحسابات المناديب", "👥 إدارة الموظفين والعملاء"]
    )
    st.markdown("---")
    st.info(f"إصدار النظام: 1.0.0\nتاريخ اليوم: {datetime.now().strftime('%Y-%m-%d')}")

# --- الأقسام الرئيسية ---

# 1. لوحة المعلومات العامة
if menu == "📊 لوحة المعلومات العامة":
    st.header("📊 ملخص أداء المنظومة")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("إجمالي الإيرادات (شامل الضريبة)", "25,400 EGP", "+12%")
    with col2:
        st.metric("عدد الرحلات المكتملة", "1,245", "50+")
    with col3:
        st.metric("صافي عمولة التطبيق", "2,540 EGP", "10%")
    with col4:
        st.metric("المناديب النشطين الآن", "18", "-2")

    st.subheader("📈 معدل الطلبات الأسبوعي")
    # بيانات تجريبية للرسم البياني
    chart_data = pd.DataFrame({
        'اليوم': ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'],
        'عدد الطلبات': [95, 110, 85, 130, 145, 190, 220]
    })
    st.line_chart(chart_data.set_index('اليوم'))

# 2. المركز المالي والضرائب (أهم جزء محاسبي)
elif menu == "💰 المركز المالي والضرائب":
    st.header("💰 الإدارة المالية والتحصيل الضريبي")
    
    st.markdown("### 📝 تفاصيل الفاتورة الضريبية النموذجية")
    test_price = st.number_input("أدخل قيمة توصيل لتجربة الحسبة (EGP):", value=100.0)
    
    v_amt = test_price * VAT_RATE
    total_bill = test_price + v_amt
    app_cut = test_price * APP_COMMISSION
    driver_net = test_price - app_cut

    c1, c2, c3, c4 = st.columns(4)
    c1.warning(f"قيمة التوصيل:\n {test_price} ج.م")
    c2.error(f"الضريبة (14%):\n {v_amt} ج.م")
    c3.success(f"المطلوب من العميل:\n {total_bill} ج.م")
    c4.info(f"صافي للسائق:\n {driver_net} ج.م")

    st.markdown("---")
    st.subheader("📋 سجل العمليات المالية الشامل")
    
    # بيانات جدولية للحسابات
    raw_data = {
        'السائق': ['أحمد محمد', 'محمود سعيد', 'ياسر علي', 'كريم جابر'],
        'أصل الخدمة': [500, 300, 450, 600],
    }
    df_finance = pd.DataFrame(raw_data)
    df_finance['ضريبة القيمة المضافة'] = df_finance['أصل الخدمة'] * VAT_RATE
    df_finance['الإجمالي من العميل'] = df_finance['أصل الخدمة'] + df_finance['ضريبة القيمة المضافة']
    df_finance['عمولة المنصة (10%)'] = df_finance['أصل الخدمة'] * APP_COMMISSION
    df_finance['مستحق للسائق'] = df_finance['أصل الخدمة'] - df_finance['عمولة المنصة (10%)']

    st.dataframe(df_finance.style.format("{:.2f}").highlight_max(axis=0, color='#ffebcc'))
    
    if st.button("📥 تحميل تقرير الضرائب (Excel/CSV)"):
        st.success("تم استخراج التقرير الضريبي بنجاح.")

# 3. تتبع وحسابات المناديب
elif menu == "🚚 تتبع وحسابات المناديب":
    st.header("🚚 مراقبة حركة المناديب")
    
    # محاكاة الخريطة
    st.markdown("#### 📍 مواقع السائقين الحالية")
    map_data = pd.DataFrame({
        'lat': [30.0444, 30.05, 30.06],
        'lon': [31.2357, 31.24, 31.25]
    })
    st.map(map_data)

    st.subheader("📋 حالة السائقين المالية")
    st.table({
        "السائق": ["هاني زكي", "عصام عمر", "ياسين طه"],
        "الحالة الحالية": ["في رحلة", "متاح", "متاح"],
        "المديونية للتطبيق": ["150 EGP", "0 EGP", "45 EGP"],
        "آخر موقع": ["الدقي", "المعادي", "الزمالك"]
    })

# 4. إدارة الموظفين والعملاء
elif menu == "👥 إدارة الموظفين والعملاء":
    st.header("👥 الهيكل الإداري وقاعدة البيانات")
    
    col_emp, col_cust = st.columns(2)
    
    with col_emp:
        with st.expander("👨‍💼 فريق العمل (الموظفين)"):
            st.write("1. **أنت** (المدير العام) - صلاحية كاملة")
            st.write("2. **محمد حسن** (المحاسب) - صلاحية مالية")
            st.write("3. **سارة أحمد** (خدمة عملاء) - صلاحية طلبات")
            if st.button("➕ إضافة موظف جديد"):
                st.text_input("اسم الموظف:")
                st.selectbox("الصلاحية:", ["مدير", "محاسب", "دعم فني"])

    with col_cust:
        with st.expander("👤 سجل كبار العملاء"):
            st.write("- عميل: فندق الماسة (50 رحلة/شهر)")
            st.write("- عميل: شركة النصر (30 رحلة/شهر)")
            st.bar_chart({"الماسة": 50, "النصر": 30, "آخرون": 120})

# تذييل الصفحة
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>نظام منجز الإداري المتكامل © 2026</p>", unsafe_allow_html=True)
