import html as html_mod
import requests
import time
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from firebase_admin import firestore
from firebase_helpers import init_firestore
from utils import send_monjez_email

# Defensive import of payment UI (may exist as a page module)
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        # alternative import if running as flat module
        from Payment_Hub import render_payment_hub  # type: ignore
    except Exception:
        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً — يرجى تفعيل صفحة Payment_Hub أو إعداد الأسرار.")
            return None

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
    try:
        ban_check = db.collection("banned_users").document(DRIVER_NAME).get()
        if ban_check and ban_check.exists:
            st.markdown("""
            <div style='background-color: black; padding: 40px; border-radius: 12px; border: 3px solid red; text-align: center; color: white;'>
                <h1 style='color: red;'>🛑 الحساب معلق أو حظر مؤقت!</h1>
                <h3>عذراً، تم تجميد حسابك مؤقتاً لمراجعة تجاوزات مالية أو مديونية متأخرة.</h3>
                <p style='color: #FFA500;'>يرجى دفع المديونية عبر المحفظة أدناه أو التواصل مع الدعم الإداري.</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
    except Exception as e:
        st.warning(f"خطأ في التحقق من حالة الحظر: {e}")

# --- 4️⃣ هيدر الكابتن / المندوب الموثق ---
st.markdown(f"""
<div style='background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; color: #333;'>
    <img src='https://cdn-icons-png.flaticon.com/512/4128/4128176.png' style='width: 80px; border-radius: 50%; border: 2px solid #1E3A8A;'>
    <h2 style='margin: 10px 0 2px 0; color: #1E3A8A;'>{DRIVER_NAME} ({role_title})</h2>
    <p style='color: #EAB308; font-size: 18px; margin: 0;'>⭐⭐⭐⭐⭐</p>
    <span style='background-color: #10B981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px;'>✔️ هوية موثقة - منصة مُنجز 2026</span>
</div>
""", unsafe_allow_html=True)

# Live Order Radar - NEW (integrates with order_lifecycles collection)
st.markdown("### 🔴 Live Order Radar - الطلبيات اللحظية")
col_radar1, col_radar2 = st.columns([3,1])
with col_radar2:
    if st.button("تحديث اللحظة 🔄", key="live_radar_refresh"):
        st.rerun()

with col_radar1:
    if db:
        try:
            pending_orders = db.collection("order_lifecycles").where("status", "==", "pending").stream()
        except Exception as e:
            st.error(f"خطأ في جلب الطلبيات اللحظية: {e}")
            pending_orders = []

        any_pending = False
        for doc in pending_orders:
            try:
                any_pending = True
                o = doc.to_dict() or {}
                o_id = doc.id
                client_name = o.get("customer_name", "عميل")
                details = o.get("order_type", "parcel")
                budget = o.get("customer_budget", o.get("customer_budget", 0) or o.get("suggested_price", "---"))

                badge_color = "#D97706" if is_courier else "#2563EB"
                st.markdown(f"""
                <div style='background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-right: 5px solid {badge_color}; margin-bottom: 10px; text-align: right;'>
                    <b style='color: #111827;'>📍 طلب مباشر من: {html_mod.escape(str(client_name))}</b><br>
                    <span style='color: #4B5563;'>📦 نوع الخدمة: {html_mod.escape(str(details))}</span><br>
                    <b style='color: #10B981;'>💵 ميزانية العميل: {html_mod.escape(str(budget))} جنيه</b>
                </div>
                """, unsafe_allow_html=True)

                # Bid input and submit (unique keys)
                bid_key = f"live_bid_input_{o_id}"
                bid_amount = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=5, value=int(budget) if isinstance(budget, (int, float)) else 20, key=bid_key)

                if st.button("🚀 إرسال عرض مباشر للطلب", key=f"live_bid_submit_{o_id}"):
                    try:
                        if not db:
                            st.error("قاعدة البيانات غير متصلة حالياً — لا يمكن إرسال العرض.")
                        else:
                            # Read current bids (defensive)
                            current = doc.to_dict() or {}
                            bids = current.get("bids", []) or []
                            new_bid = {
                                "driver_name": DRIVER_NAME,
                                "driver_id": DRIVER_PHONE,
                                "bid_amount": float(bid_amount),
                                "timestamp": datetime.now().isoformat(),  # ✅ تم التعديل هنا لتفادي خطأ Firestore Sentinel
                                "bid_status": "active"
                            }
                            bids.append(new_bid)
                            db.collection("order_lifecycles").document(o_id).update({"bids": bids})
                            st.success(f"🟢 تم إرسال عرضك بقيمة {bid_amount} جنيه بنجاح! بانتظار موافقة العميل.")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"فشل في إرسال العرض: {e}")
            except Exception:
                continue

        if not any_pending:
            st.info("📭 لا توجد طلبيات جديدة في الرادار حالياً.")

st.markdown("---")

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
        try:
            live_orders = db.collection("orders").where("status", "in", ["processing", "معلق - بانتظار سائق"]).stream()
        except Exception as e:
            st.error(f"خطأ في جلب الطلبيات: {e}")
            live_orders = []
        order_count = 0
        
        for doc in live_orders:
            try:
                o_data = doc.to_dict() or {}
                o_id = doc.id
                service_type = o_data.get("service_type", "")

                if is_courier and service_type in ["standard_ride", "comfort_ride"]:
                    continue
                elif not is_courier and service_type == "express_bike":
                    continue

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
                    try:
                        if not db:
                            st.error("قاعدة البيانات غير متصلة حالياً — لا يمكن إرسال العرض.")
                        else:
                            db.collection("orders").document(o_id).update({
                                "status": "🚖 جاري الاستلام",
                                "driver_assigned": DRIVER_NAME,
                                "driver_phone": DRIVER_PHONE,
                                "suggested_price": custom_bid
                            })
                            st.success(f"🟢 تم إرسال عرضك بقيمة {custom_bid} جنيه بنجاح! بانتظار موافقة العميل.")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"فشل في إرسال العرض إلى السيرفر: {e}")
            except Exception:
                continue
                
        if order_count == 0:
            st.info(f"📭 الميدان هادئ الآن. لا توجد طلبات متوافقة مع تخصص ({role_title}) حالياً.")

# ---------------------------------------------------------
# 📍 التبويب الثاني: الشحنة الحالية وتنفيذ المهمة الفورية
# ---------------------------------------------------------
with driver_tabs[1]:
    st.markdown("#### 📍 شاشة التنفيذ وتتبع المهمة الحالية")
    
    # --- My Current Orders (integrated with order_lifecycles) ---
    st.markdown("##### 🧭 طلباتي الحالية")
    if db:
        try:
            active_missions = db.collection("order_lifecycles").where("assigned_driver", "==", DRIVER_NAME).stream()
        except Exception as e:
            st.error(f"خطأ في جلب المهمات النشطة: {e}")
            active_missions = []
        mission_count = 0
        
        for doc in active_missions:
            try:
                m_data = doc.to_dict() or {}
                m_id = doc.id
                status = m_data.get("status")
                mission_count += 1

                st.markdown(f"""
                <div style='background-color: #111827; padding: 20px; border-radius: 10px; color: white; text-align: right; margin-bottom: 15px;'>
                    <h3 style='color: #38BDF8; margin: 0;'>{vehicle_icon} مهمة حالية</h3>
                    <p style='margin: 8px 0;'><b>👤 الاسم:</b> {html_mod.escape(str(m_data.get('customer_name', '')))}</p>
                    <p style='margin: 8px 0;'><b>📦 التفاصيل:</b> {html_mod.escape(str(m_data.get('order_type', '')))} - {html_mod.escape(str(m_data.get('pickup_location', '')))} → {html_mod.escape(str(m_data.get('destination_location', '')))}</p>
                    <hr style='border-color: #374151;'>
                    <b style='color: #FBBF24; font-size: 16px;'>💰 القيمة المتفق عليها: {m_data.get('final_price') or m_data.get('customer_budget')}.00 جنيه</b><br>
                    <small style='color: #9CA3AF;'>🚨 حالة المهمة الحية: {status}</small>
                </div>
                """, unsafe_allow_html=True)

                # State change buttons (follow lifecycle): pending -> bid_accepted -> picked_up -> in_transit -> delivered
                if status == "bid_accepted":
                    if st.button("📦 تم الاستلام من المرسل/الموكل", key=f"btn_picked_{m_id}"):
                        try:
                            db.collection("order_lifecycles").document(m_id).update({"status": "picked_up", "picked_up_at": firestore.SERVER_TIMESTAMP})
                            st.success("🔔 تم تأكيد الاستلام. انتقل الطلب إلى حالة 'PICKED_UP'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل تحديث الحالة: {e}")
                elif status == "picked_up":
                    if st.button("🚴 في الطريق للعميل - بدء التتبع", key=f"btn_transit_{m_id}"):
                        try:
                            db.collection("order_lifecycles").document(m_id).update({"status": "in_transit", "in_transit_at": firestore.SERVER_TIMESTAMP})
                            st.success("🚚 تم تحديث الحالة إلى 'IN_TRANSIT'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل تحديث الحالة: {e}")
                elif status == "in_transit":
                    if st.button("✅ تم التوصيل وتسوية المبلغ", key=f"btn_delivered_{m_id}"):
                        try:
                            db.collection("order_lifecycles").document(m_id).update({"status": "delivered", "delivered_at": firestore.SERVER_TIMESTAMP})
                            st.success("🎉 تم تسليم الطلب وتسجيله كـ 'DELIVERED'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل تحديث الحالة: {e}")
                else:
                    st.info(f"حالة المهمة الحالية: {status}")

            except Exception:
                continue
                
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
        # Prefer opening unified payment hub if Secrets are not configured here
        paymob_api_key = None
        try:
            paymob_api_key = st.secrets.get("paymob", {}).get("PAYMOB_API_KEY")
        except Exception:
            paymob_api_key = None

        if not paymob_api_key:
            st.info("⚠️ لم يتم تكوين مفاتيح Paymob هنا — سيتم فتح مركز الدفع الموحد.")
            try:
                render_payment_hub(purpose="debt", default_amount=int(topup_amount))
            except Exception as e:
                st.error(f"تعذر فتح بوابة الدفع: {e}")
        else:
            # proceed with the original Paymob flow but fully defensive
            try:
                integration_id = st.secrets.get("paymob", {}).get("PAYMOB_INTEGRATION_ID")
                iframe_id = st.secrets.get("paymob", {}).get("PAYMOB_IFRAME_ID")

                # 1. المصادقة واستخراج الـ Auth Token
                auth_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": paymob_api_key}, timeout=15)
                auth_res.raise_for_status()
                auth_token = auth_res.json().get("token")
                if not auth_token:
                    st.error("تعذر الحصول على توكن المصادقة من Paymob.")
                else:
                    # 2. إنشاء الطلب لدى Paymob
                    order_payload = {
                        "auth_token": auth_token,
                        "delivery_needed": "false",
                        "amount_cents": str(int(topup_amount * 100)),
                        "currency": "EGP",
                        "merchant_order_id": f"TOPUP-{user_data.get('role', 'driver').upper()}-{int(time.time())}"
                    }
                    order_res = requests.post(
                        "https://accept.paymob.com/api/ecommerce/orders",
                        json=order_payload,
                        timeout=15
                    )
                    order_res.raise_for_status()
                    order_id = order_res.json().get("id")

                    # 3. استخراج مفتاح الدفع (Payment Key)
                    first_name = DRIVER_NAME.split()[0] if DRIVER_NAME else "Driver"
                    last_name = DRIVER_NAME.split()[-1] if len(DRIVER_NAME.split()) > 1 else "Monjez"

                    payment_key_payload = {
                        "auth_token": auth_token,
                        "amount_cents": str(int(topup_amount * 100)),
                        "expiration": 3600,
                        "order_id": order_id,
                        "billing_data": {
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": "driver@monjez.online",
                            "phone_number": DRIVER_PHONE,
                            "apartment": "NA", "floor": "NA", "street": "NA",
                            "building": "NA", "shipping_method": "NA", "postal_code": "NA",
                            "city": "Cairo", "country": "EGP", "state": "Cairo"
                        },
                        "currency": "EGP",
                        "integration_id": int(integration_id) if integration_id else None
                    }

                    payment_key_res = requests.post(
                        "https://accept.paymob.com/api/acceptance/payment_keys",
                        json=payment_key_payload,
                        timeout=15
                    )
                    payment_key_res.raise_for_status()
                    payment_token = payment_key_res.json().get("token")

                    if iframe_id and payment_token:
                        st.session_state["paymob_iframe_url"] = f"https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?token={payment_token}"
                        st.success("✅ تم التجهيز بنجاح! أدخل بيانات البطاقة أدناه لإتمام الشحن:")
                    else:
                        st.error("❌ فشل تجهيز واجهة الدفع. يرجى التحقق من إعدادات Paymob في الأسرار.")
            except requests.exceptions.RequestException as e:
                st.error(f"خطأ شبكي أثناء الاتصال بـ Paymob: {e}")
            except Exception as e:
                st.error(f"❌ خطأ في عملية الشحن: {e}")

    # --- 🖥️ عرض شاشة البطاقة المباشرة داخل التطبيق ---
    if "paymob_iframe_url" in st.session_state:
        st.markdown("---")
        st.markdown("##### 🔒 بوابة الدفع الآمنة (أدخل بيانات البطاقة)")
        
        components.html(
            f"""
            <iframe 
                src="{st.session_state['paymob_iframe_url']}" 
                width="100%" 
                height="650" 
                frameborder="0" 
                allow="geolocation">
            </iframe>
            """,
            height=670
        )

    st.markdown("---")
    st.markdown("#### 🛠️ مركز المساعدة والدعم المباشر")
    st.caption("تواصل مع غرفة عمليات منصة منجز للإبلاغ عن مشاكل الميدان أو توثيق الرحلات الكاش.")
