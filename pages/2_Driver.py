import html as html_mod
import requests
import time
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore
from utils import send_monjez_email

st.set_page_config(page_title="منصة مُنجز - بوابة الميدان", layout="wide", initial_sidebar_state="expanded")

# --- 1️⃣ الاتصال الآمن بالفايربيز ---
db = init_firestore()
if db is None:
    st.error("❌ فشل اتصال السيرفر مع قاعدة البيانات")

# --- 2️⃣ استخراج بيانات المستخدم الحالي والدور (سائق أم مندوب) ---
user_data = st.session_state.get("user_data", {
    "name": "ahmed mostafa mohammed",
    "phone": "+201000000000",
    "role": "driver"  # خيارات: 'driver' (سائق) أو 'courier' (مندوب)
})

DRIVER_NAME = user_data.get("name", "ahmed mostafa mohammed")
DRIVER_PHONE = user_data.get("phone", "+201000000000")

# مفتاح اختيار الدور في أعلى الصفحة للاختبار والتنقل السريع
st.sidebar.markdown("### 🎛️ وضع التشغيل الميداني")
worker_role = st.sidebar.radio(
    "حدد طبيعة عملك اليوم:",
    ["🚖 كابتن (سائق تاكسي / ملاكي)", "🏍️ مرسول (مندوب طرود وسريع)"],
    index=0 if user_data.get("role") == "driver" else 1
)

is_courier = "مندوب" in worker_role
role_title = "المندوب" if is_courier else "الكابتن"
vehicle_icon = "🏍️" if is_courier else "🚖"

# --- 3️⃣ رادار فحص قائمة الحظر الفورية لمنع النصب والاحتيال ---
if db:
    ban_check = db.collection("banned_users").document(DRIVER_NAME).get()
    if ban_check.exists:
        st.markdown("""
        <div style='background-color: black; padding: 40px; border-radius: 12px; border: 3px solid red; text-align: center; color: white;'>
            <h1 style='color: red;'>🛑 الحساب معلق أو حظر مؤقت!</h1>
            <h3>عذراً، تم تجميد حسابك مؤقتاً لمراجعة تجاوزات مالية أو مديونية متأخرة.</h3>
            <p style='color: #FFA500;'>يرجى دفع المديونية عبر المحفظة أدناه أو التواصل مع الدعم الإداري.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

# --- 4️⃣ هيدر الكابتن / المندوب الموثق ---
st.markdown(f"""
<div style='background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; color: #333;'>
    <img src='https://cdn-icons-png.flaticon.com/512/4128/4128176.png' style='width: 80px; border-radius: 50%; border: 2px solid #1E3A8A;'>
    <h2 style='margin: 10px 0 2px 0; color: #1E3A8A;'>{DRIVER_NAME} ({role_title})</h2>
    <p style='color: #EAB308; font-size: 18px; margin: 0;'>⭐⭐⭐⭐⭐</p>
    <span style='background-color: #10B981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;'>✔️ هوية موثقة - منصة مُنجز 2026</span>
</div>
""", unsafe_allow_html=True)

# العدادات الرقمية المحددة لكل دور
st.markdown("###")
col_metric1, col_metric2 = st.columns(2)
with col_metric1:
    metric_label = "📦 الطرود الموصلة" if is_courier else "📊 الرحلات المكتملة"
    st.metric(label=metric_label, value="3,536 مهمة")
with col_metric2:
    st.metric(label="💰 إجمالي الإيرادات", value="340,904.74 ج.م")

st.markdown("---")

# الرصيد المالي المتاح والمديونية
current_balance = -160.96  # رصيد تجريبي سلبي

st.markdown(f"""
<div style='background-color: #FEF2F2; padding: 15px; border-radius: 8px; border: 1px solid #FCA5A5; display: flex; justify-content: space-between; align-items: center; direction: rtl;'>
    <span style='color: #991B1B; font-weight: bold; font-size: 16px;'>📉 رصيد الحساب الحالي:</span>
    <span style='color: #DC2626; font-weight: bold; font-size: 18px;'>{current_balance:.2f} جنيه</span>
</div>
""", unsafe_allow_html=True)

st.write("#")

# --- 5️⃣ تبويبات التحكم الرئيسية ---
driver_tabs = st.tabs([
    f"📥 استلام الطلبات المتاحة ({role_title})", 
    "📍 المهمة الحالية والتنفيذ", 
    "💳 المحفظة والدعم الفني"
])

# ---------------------------------------------------------
# 📥 التبويب الأول: استلام ورادار الطلبات الميدانية
# ---------------------------------------------------------
with driver_tabs[0]:
    st.markdown(f"#### 📥 طلبات الميدان المتاحة لـ {role_title}")
    
    if db:
        # جلب الطلبات بانتظار سائق/مندوب
        live_orders = db.collection("orders").where("status", "in", ["processing", "معلق - بانتظار سائق"]).stream()
        order_count = 0
        
        for doc in live_orders:
            o_data = doc.to_dict()
            o_id = doc.id
            service_type = o_data.get("service_type", "")
            
            # فلترة طلبات المندوب (موتوسيكل/طرود) عن طلبات السائق (تاكسي/ملاكي)
            if is_courier and service_type in ["standard_ride", "comfort_ride"]:
                continue  # المندوب يتخطى طلبات التاكسي
            elif not is_courier and service_type == "express_bike":
                continue  # سائق التاكسي يتخطى طلبات الطرود الصغرى

            order_count += 1
            badge_color = "#D97706" if is_courier else "#2563EB"
            
            st.markdown(f"""
            <div style='background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-right: 5px solid {badge_color}; margin-bottom: 10px; text-align: right;'>
                <b style='color: #111827;'>📍 طلب {vehicle_icon} من: {html_mod.escape(str(o_data.get('client_name', 'عميل منجز')))}</b><br>
                <span style='color: #4B5563;'>📦 التفاصيل والوجهة: {html_mod.escape(str(o_data.get('order_details', '')))}</span><br>
                <b style='color: #10B981;'>💵 ميزانية العميل المقترحة: {html_mod.escape(str(o_data.get('suggested_price', 30)))} جنيه</b>
            </div>
            """, unsafe_allow_html=True)
            
            custom_bid = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=10, value=int(o_data.get('suggested_price', 30)), key=f"num_input_{o_id}")
            
            if st.button(f"🚀 إرسال العرض المالي للعميل كـ {role_title}", key=f"submit_bid_btn_{o_id}", use_container_width=True):
                db.collection("orders").document(o_id).update({
                    "status": "🚖 جاري الاستلام",
                    "driver_assigned": DRIVER_NAME,
                    "driver_phone": DRIVER_PHONE,
                    "suggested_price": custom_bid
                })
                st.success(f"🟢 تم إرسال عرضك بقيمة {custom_bid} جنيه بنجاح! بانتظار موافقة العميل.")
                time.sleep(1)
                st.rerun()
                
        if order_count == 0:
            st.info(f"📭 الميدان هادئ الآن. لا توجد طلبات متوافقة مع تخصص ({role_title}) حالياً.")

# ---------------------------------------------------------
# 📍 التبويب الثاني: الشحنة الحالية وتنفيذ المهمة الفورية
# ---------------------------------------------------------
with driver_tabs[1]:
    st.markdown("#### 📍 شاشة التنفيذ وتتبع المهمة الحالية")
    
    if db:
        active_missions = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).stream()
        mission_count = 0
        
        for doc in active_missions:
            m_data = doc.to_dict()
            m_id = doc.id
            status = m_data.get("status")
            
            if status in ["🚖 جاري الاستلام", "🚚 جاري التوصيل", "✅ في انتظار تقييم الطرفين"]:
                mission_count += 1
                
                st.markdown(f"""
                <div style='background-color: #111827; padding: 20px; border-radius: 10px; color: white; text-align: right; margin-bottom: 15px;'>
                    <h3 style='color: #38BDF8; margin: 0;'>{vehicle_icon} العميل بانتظارك</h3>
                    <p style='margin: 8px 0;'><b>👤 الاسم:</b> {html_mod.escape(str(m_data.get('client_name', '')))}</p>
                    <p style='margin: 8px 0;'><b>📦 الوجهة/الشحنة:</b> {html_mod.escape(str(m_data.get('order_details', '')))}</p>
                    <hr style='border-color: #374151;'>
                    <b style='color: #FBBF24; font-size: 16px;'>💰 القيمة المتفق عليها: {m_data.get('suggested_price')}.00 جنيه</b><br>
                    <small style='color: #9CA3AF;'>🚨 حالة المهمة الحية: {status}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # مرحلة 1: استلام الطلب
                if status == "🚖 جاري الاستلام":
                    if st.button("📦 تم استلام العميل/الشحنة والتحرك", key=f"status_btn_pickup_{m_id}", use_container_width=True):
                        db.collection("orders").document(m_id).update({"status": "🚚 جاري التوصيل"})
                        st.rerun()
                        
                # مرحلة 2: إنهاء التوصيل وإرسال الفاتورة
                elif status == "🚚 جاري التوصيل":
                    if st.button("🏁 إنهاء وتسليم الطلب بنجاح للوجهة", key=f"status_btn_deliver_{m_id}", use_container_width=True):
                        # تحديث الفايربيز
                        db.collection("orders").document(m_id).update({"status": "✅ في انتظار تقييم الطرفين"})
                        
                        # إرسال الفاتورة الرسمية للعميل بريدياً
                        invoice_html = f"""
                        <div style="direction: rtl; text-align: right; font-family: sans-serif; border: 2px solid #10B981; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #10B981;">📋 فاتورة معتمدة من منصة مُنجز 2026</h2>
                            <p>عزيزي <b>{m_data.get('client_name')}</b>، تم إنهاء طلبك بنجاح.</p>
                            <hr>
                            <p><b>{role_title} المسؤول:</b> {DRIVER_NAME}</p>
                            <p><b>📦 تفاصيل الخدمة:</b> {m_data.get('order_details')}</p>
                            <p style="font-size: 18px; color: #1E3A8A;"><b>💰 الإجمالي المطلوب سداده: {m_data.get('suggested_price')} جنيه</b></p>
                            <hr>
                            <p style="font-size: 12px; color: #6B7280; text-align: center;">شكراً لاستخدامك منصة منجز الذكية ✨</p>
                        </div>
                        """
                        client_email = m_data.get("client_email", "")
                        if client_email:
                            send_monjez_email(client_email, f"📦 فاتورة طلبك عبر منصة مُنجز ({role_title})", invoice_html)
                        
                        st.success("🎯 تم إنهاء المشوار وإرسال الفاتورة الإلكترونية للعميل بنجاح!")
                        st.rerun()
                        
                # مرحلة 3: التقييم وإغلاق المعاملة
                elif status == "✅ في انتظار تقييم الطرفين":
                    st.warning("🏁 الرحلة وصلت. فضلاً قيّم العميل لإغلاق الحساب وتقييد العمولات:")
                    rating = st.slider("⭐ تقييم سلوك العميل:", 1, 5, 5, key=f"slider_rating_{m_id}")
                    if st.button("💾 حفظ وإغلاق الفاتورة النهائية", key=f"save_final_invoice_{m_id}", use_container_width=True):
                        db.collection("orders").document(m_id).update({"status": "⭐ تم الإغلاق والتقييم بالكامل"})
                        st.success("🎯 تم تسوية الحساب وإغلاق المعاملة بنجاح!")
                        st.rerun()
                        
        if mission_count == 0:
            st.info(f"🚖 لا توجد لديك أي رحلات أو شحنات نشطة جاري تنفيذها حالياً كـ {role_title}.")

# ---------------------------------------------------------
# 🛠️ التبويب الثالث: المحفظة والشحن وتسديد المديونية + الدعم
# ---------------------------------------------------------
with driver_tabs[2]:
    st.markdown("#### 💳 المحفظة والشحن الإلكتروني عبر Paymob")
    
    st.write(f"رصيدك الحالي: **{current_balance:.2f} ج.م**")
    if current_balance < 0:
        st.error(f"⚠️ يوجد عليك مديونية متأخرة بقيمة {abs(current_balance):.2f} ج.م. يرجى الشحن لتفادي تجميد الحساب.")

    topup_amount = st.number_input("حدد مبلغ الشحن لتسديد المديونية أو شحن الرصيد (ج.م):", min_value=10, value=200, step=10)
    
    if st.button("💳 بدء عملية الدفع والشحن عبر Paymob", use_container_width=True):
        try:
            api_key = st.secrets["paymob"]["PAYMOB_API_KEY"]
            auth_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": api_key})
            auth_res.raise_for_status()
            auth_token = auth_res.json().get("token")
            
            order_res = requests.post(
                "https://accept.paymob.com/api/ecommerce/orders",
                json={
                    "auth_token": auth_token,
                    "delivery_needed": "false",
                    "amount_cents": str(int(topup_amount * 100)),
                    "currency": "EGP",
                    "merchant_order_id": f"TOPUP-{user_data.get('role', 'driver').upper()}-{int(time.time())}"
                }
            )
            order_res.raise_for_status()
            st.success("✅ تم الاتصال بـ Paymob وإنشاء المعاملة المباشرة للشحن بنجاح!")
        except Exception as e:
            st.error(f"❌ خطأ في عملية الشحن: {e}")

    st.markdown("---")
    st.markdown("#### 🛠️ مركز المساعدة والدعم المباشر")
    st.caption("تواصل مع غرفة عمليات منصة منجز للإبلاغ عن مشاكل الميدان أو توثيق الرحلات الكاش.")
