import html as html_mod
import requests
import time
import streamlit as st
from firebase_admin import firestore
from firebase_helpers import init_firestore

st.set_page_config(page_title="منصة مُنجز - بوابة العميل", layout="wide", initial_sidebar_state="expanded")

# --- الاتصال الآمن بالفايربيز ---
db = init_firestore()
if db is None:
    st.error("❌ اتصال السيرفر معطل")

# --- بروفايل العميل الجانبي (DiDi Style) ---
st.sidebar.markdown("""
<div style='text-align: center; background-color: #F3F4F6; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
    <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' style='width: 75px; border-radius: 50%; border: 2px solid #1E3A8A;'>
    <h3 style='margin: 10px 0 2px 0; color: #1E3A8A;'>AHMED mostafa</h3>
    <a href='#' style='text-decoration: none; color: #6B7280; font-size: 13px;'>تعديل المعلومات الشخصية ✏️</a>
</div>
""", unsafe_allow_html=True)

# قائمة التحكم المتطابقة مع الواجهة
client_menu = st.sidebar.radio("📌 انتقل إلى:", [
    "🚖 اطلب مشوار / توصيل الآن", 
    "📜 مشاويري السابقة", 
    "💳 محفظة الدفع الإلكتروني", 
    "🛡️ مركز السلامة والطوارئ",
    "⚙️ إعدادات التطبيق"
])

# ---------------------------------------------------------
# 1️⃣ قسم طلب المشوار والتوصيل
# ---------------------------------------------------------
if client_menu == "🚖 اطلب مشوار / توصيل الآن":
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🛒 طلب خدمة توصيل ومزايدة حية</h2>", unsafe_allow_html=True)
    
    # واجهة إدخال الطلب المحدثة
    with st.form("new_order_form", clear_on_submit=True):
        # خدمة صريحة بالاختيار (Ride vs Delivery)
        service_option = st.selectbox(
            "اختر نوع الخدمة:",
            [
                "🚖 طلب تاكسي / توصيل أفراد",
                "📦 توصيل طرود / مرسول (أطلب أي شيء)"
            ]
        )

        c_name = st.text_input("👤 اسم العميل الافتراضي", value="أحمد مصطفى")
        o_details = st.text_area("📝 ما الذي تريد توصيله؟ (اكتب تفاصيل الوجهة والشحنة بدقة)", placeholder="مثال: مطلوب استلام طرد من العنوان X وتسليمه إلى Y، الوزن التقريبي 2 كجم، حساس")
        s_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30, step=5)
        c_phone = st.text_input("📱 رقم هاتف التواصل الحركي", value="+20 1000000000")

        # --- Wallet guard: attempt to fetch user's wallet balance from users collection ---
        wallet_balance = None
        if db:
            try:
                # Attempt to find a user document matching the provided name
                users_q = db.collection("users").where("full_name", "==", c_name).limit(1).get()
                if users_q and len(users_q) > 0:
                    user_doc = users_q[0]
                    user_data = user_doc.to_dict()
                    wallet_balance = user_data.get("wallet_balance", 0.0)
                else:
                    # try alternative field
                    users_q2 = db.collection("users").where("name", "==", c_name).limit(1).get()
                    if users_q2 and len(users_q2) > 0:
                        user_doc = users_q2[0]
                        user_data = user_doc.to_dict()
                        wallet_balance = user_data.get("wallet_balance", 0.0)
                    else:
                        wallet_balance = 0.0
            except Exception:
                wallet_balance = 0.0

        # Display balance and warnings inline (but keep styling intact)
        if wallet_balance is None:
            st.info("رصيد المحفظة: غير متوفر حالياً")
        else:
            st.metric("الرصيد الحالي لمحفظتك", f"{wallet_balance} ج.م")
            # Warn if negative balance -> block submission later
            if isinstance(wallet_balance, (int, float)) and wallet_balance < 0:
                st.warning("⚠️ رصيد محفظتك سالب. لا يمكنك إرسال طلبات حتى تتم عملية شحن المحفظة.")

            # Warn if estimated fare (suggested price) is higher than balance
            if isinstance(wallet_balance, (int, float)) and wallet_balance < float(s_price):
                st.warning("⚠️ رصيدك الحالي أقل من السعر التقديري للرحلة؛ قد تحتاج لشحن المحفظة قبل التأكيد.")

        submit_btn = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض السائقين")
        
        if submit_btn and db:
            if o_details.strip() == "":
                st.warning("⚠️ يرجى كتابة تفاصيل الشحنة أولاً قبل النشر!")
            else:
                # Block submission if wallet balance is explicitly negative
                if wallet_balance is not None and isinstance(wallet_balance, (int, float)) and wallet_balance < 0:
                    st.error("❌ تم إيقاف إرسال الطلب لأن رصيد المحفظة سالب. يرجى شحن المحفظة أولاً.")
                else:
                    # Build payload common fields
                    payload = {
                        "client_name": c_name,
                        "order_details": o_details,
                        "suggested_price": s_price,
                        "phone": c_phone,
                        "status": "processing",
                        "driver_assigned": "",
                        "timestamp": firestore.SERVER_TIMESTAMP,
                    }

                    try:
                        if service_option == "🚖 طلب تاكسي / توصيل أفراد":
                            # save under rides collection
                            db.collection("rides").add(payload)
                        else:
                            # save under deliveries collection
                            db.collection("deliveries").add(payload)

                        st.success("🎯 عظيم يا هندسة! تم قيد ونشر طلبك في الميدان بنجاح.")
                    except Exception as e:
                        st.error(f"❌ حدث خطأ أثناء حفظ الطلب: {e}")

    # رادار تتبع الحالات النشطة
    st.markdown("---")
    st.markdown("<h3 style='color: #10B981; text-align: right;'>📋 مراقبة وتتبع طلباتك الحالية</h3>", unsafe_allow_html=True)
    
    if db:
        # Check both collections for active orders for this client
        orders_stream = list(db.collection("orders").where("client_name", "==", "أحمد مصطفى").stream())
        rides_stream = list(db.collection("rides").where("client_name", "==", "أحمد مصطفى").stream())
        deliveries_stream = list(db.collection("deliveries").where("client_name", "==", "أحمد مصطفى").stream())

        active_found = False
        for doc in orders_stream + rides_stream + deliveries_stream:
            data = doc.to_dict()
            status = data.get("status")
            if status != "⭐ تم الإغلاق والتقييم بالكامل":
                active_found = True
                driver = data.get("driver_assigned", "جاري البحث عن كابتن...")
                price = data.get("suggested_price", 30)
                st.markdown(f"""
                <div style='background-color: #EFF6FF; padding: 15px; border-radius: 8px; border-right: 5px solid #3B82F6; margin-bottom: 10px; text-align: right;'>
                    <b style='color: #1E3A8A; font-size: 16px;'>✔️ تم قبول طلبك وبدأ التنفيذ الحقيقي!</b><br>
                    <span style='color: #333;'>👤 الكابتن المسؤول: {html_mod.escape(str(driver)) if driver else 'جاري الاستلام'}</span><br>
                    <span style='color: #333;'>💰 السعر المتفق عليه: {html_mod.escape(str(price))} جنيه</span><br>
                    <span style='color: #DC2626;'>🚨 حالة التحرك الحية الآن: 🚖 {html_mod.escape(str(status))}</span>
                </div>
                """, unsafe_allow_html=True)

        if not active_found:
            st.info("💡 لا توجد لديك طلبات نشطة في الوقت الحالي. رحلاتك القادمة ستظهر هنا فورا.")

# ---------------------------------------------------------
# 2️⃣ قسم سجل المشاوير
# ---------------------------------------------------------
elif client_menu == "📜 مشاويري السابقة":
    st.subheader("📜 دفتر سجل رحلاتك")
    st.caption("يتيح لك مراجعة الأماكن والأسعار السابقة لرحلاتك مع منجز.")

# ---------------------------------------------------------
# 3️⃣ قسم المحفظة واختبار الربط مع Paymob
# ---------------------------------------------------------
elif client_menu == "💳 محفظة الدفع الإلكتروني":
    st.subheader("💳 رصيد حسابك الذكي")
    st.metric("الرصيد المتاح للعميل", "0.00 ج.م")
    st.markdown("---")
    
    st.subheader("🚀 اختبار الشحن والتكامل مع Paymob")
    amount = st.number_input("حدد مبلغ الشحن التجريبي (ج.م):", min_value=10, value=50, step=10)
    
    if st.button("💳 بدء تجربة الاتصال والدفع عبر Paymob"):
        try:
            # 1. قراءة المفاتيح من st.secrets
            api_key = st.secrets["paymob"]["PAYMOB_API_KEY"]
            
            # 2. المصادقة للحصول على Auth Token
            auth_res = requests.post(
                "https://accept.paymob.com/api/auth/tokens",
                json={"api_key": api_key}
            )
            auth_res.raise_for_status()
            auth_token = auth_res.json().get("token")
            
            # 3. إنشاء طلب جديد (Order) رقم المعاملة باستخدام وقت النظام الحقيقي
            order_res = requests.post(
                "https://accept.paymob.com/api/ecommerce/orders",
                json={
                    "auth_token": auth_token,
                    "delivery_needed": "false",
                    "amount_cents": str(int(amount * 100)),
                    "currency": "EGP",
                    "merchant_order_id": f"TOPUP-CLIENT-{int(time.time())}"
                }
            )
            order_res.raise_for_status()
            paymob_order_id = order_res.json().get("id")
            
            st.success("✅ تم الاتصال بـ Paymob بنجاح والمفاتيح شغالة تمام 100%!"
            )
            st.info(f"🆔 رقم المعاملة المولد من Paymob: `{paymob_order_id}`")
            
        except KeyError:
            st.error("❌ لم يتم العثور على مفاتيح Paymob داخل secrets.toml! تأكد من حفظ قسم [paymob].")
        except Exception as e:
            st.error(f"❌ خطأ أثناء الاتصال بـ Paymob: {e}")

# ---------------------------------------------------------
# 4️⃣ قسم الطوارئ والسلامة
# ---------------------------------------------------------
elif client_menu == "🛡️ مركز السلامة والطوارئ":
    st.subheader("🛡️ نظام الأمان والسلامة")
    st.error("🚨 زر الاستغاثة (SOS): بمجرد الضغط عليه، يتم إرسال موقعك الجغرافي الحي فوراً لغرفة عمليات وموظفي منجز...")

# ---------------------------------------------------------
# 5️⃣ قسم إعدادات التطبيق
# ---------------------------------------------------------
elif client_menu == "⚙️ إعدادات التطبيق":
    st.subheader("⚙️ تفضيلات المستخدم والخصومات")
