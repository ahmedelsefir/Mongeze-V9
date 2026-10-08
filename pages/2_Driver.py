import html as html_mod
import requests
import time
from datetime import datetime, timezone
import logging

import streamlit as st

# ⚠️ يجب أن تكون st.set_page_config أول أمر Streamlit في الملف تماماً
st.set_page_config(
    page_title="منصة مُنجز - بوابة الميدان", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# استيرادات آمنة لتفادي إيقاف السيرفر في حال عدم توفر الموديول
try:
    from firebase_admin import firestore
except Exception:
    firestore = None

try:
    from firebase_helpers import init_firestore
except Exception:
    def init_firestore():
        return None

try:
    from utils import send_monjez_email
except Exception:
    def send_monjez_email(*args, **kwargs):
        pass

# استيراد واجهة الدفع بشكل محمي
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub  # type: ignore
    except Exception:
        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً — يرجى تفعيل صفحة Payment_Hub أو إعداد الأسرار.")
            return None

# --- دالة رفع مستندات السائق - النسخة النهائية المحمية ---
def upload_driver_docs(
    driver_phone: str,
    driver_name: str,
    uploaded_files: dict,
    db=None,
    storage_bucket=None,
) -> dict:
    try:
        if not driver_phone:
            return {"success": False, "message": "رقم الهاتف مطلوب.", "urls": {}}

        doc_id = driver_phone.strip().replace("+", "")

        if db is None:
            from firebase_helpers import init_firestore
            db = init_firestore(notify=False)

        if db is None:
            return {"success": False, "message": "قاعدة البيانات غير متاحة.", "urls": {}}

        storage_urls = {}
        if storage_bucket is None:
            try:
                from firebase_admin import storage
                # التعديل الأهم: يقرأ الباكت من الأسرار اللي انت حميتها
                bucket_name = st.secrets["firebase"]["storage_bucket"]
                storage_bucket = storage.bucket(bucket_name)
            except Exception as e:
                logger.warning(f"Storage unavailable: {e}")
                storage_bucket = None

        required_keys = ["front_id", "back_id", "vehicle_front", "vehicle_back", "license_front", "license_back"]

        for file_key in required_keys:
            uploaded_file = uploaded_files.get(file_key)
            if uploaded_file is None:
                continue
            if not hasattr(uploaded_file, "read"):
                continue

            file_name = getattr(uploaded_file, "name", f"{file_key}.jpg")
            file_ext = file_name.split(".")[-1].lower() if "." in file_name else "jpg"
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            storage_path = f"driver_docs/{doc_id}/{file_key}_{timestamp}.{file_ext}"

            try:
                uploaded_file.seek(0)
                if storage_bucket is not None:
                    blob = storage_bucket.blob(storage_path)
                    blob.upload_from_string(
                        uploaded_file.read(),
                        content_type=getattr(uploaded_file, "type", "image/jpeg")
                    )
                    storage_urls[file_key] = storage_path
                else:
                    storage_urls[file_key] = storage_path
            except Exception as e:
                logger.error(f"Upload failed for {file_key}: {e}")
                return {"success": False, "message": f"فشل رفع {file_key}: {e}", "urls": storage_urls}

        # التعديل التاني: بيرجع الـ urls بس، والـ set بيتعمل مرة واحدة في الفورم
        return {
            "success": True,
            "message": "تم رفع مستندات التوثيق بنجاح، وجار مراجعة الحساب.",
            "urls": storage_urls,
        }

    except Exception as e:
        logger.exception(f"upload_driver_docs exception: {e}")
        return {"success": False, "message": f"خطأ غير متوقع: {e}", "urls": {}}

# --- 1️⃣ الاتصال الآمن بالفايربيز ---
db = init_firestore()
if db is None:
    st.error("❌ فشل اتصال السيرفر مع قاعدة البيانات")

# --- 2️⃣ استخراج بيانات المستخدم الحالي والدور (سائق أم مندوب) ---
user_data = st.session_state.get("user_data", {
    "name": "ahmed mostafa mohammed",
    "phone": "+201000000000",
    "role": "driver"
})

DRIVER_NAME = user_data.get("name", "ahmed mostafa mohammed")
DRIVER_PHONE = user_data.get("phone", "+201000000000")

# --- مفتاح اختيار الدور ---
st.sidebar.markdown("### 🎛️ وضع التشغيل الميداني")
worker_role = st.sidebar.radio(
    "حدد طبيعة عملك اليوم:",
    ["🚖 كابتن (سائق تاكسي / ملاكي)", "🏍️ مرسول (مندوب طرود وسريع)"],
    index=0 if user_data.get("role") == "driver" else 1
)

is_courier = "مندوب" in worker_role
role_title = "المندوب" if is_courier else "الكابتن"
vehicle_icon = "🏍️" if is_courier else "🚖"

# --- 📍 GPS Live Tracking - النسخة النهائية المتحركة ---
try:
    from streamlit_js_eval import streamlit_js_eval
    
    # يجيب موقعك الحقيقي من المتصفح
    loc = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                err => resolve({lat: 30.0444, lon: 31.2357})
            );
        })
        """,
        key="get_loc"
    )
    
    if loc and isinstance(loc, dict):
        lat = loc.get("lat", 30.0444)
        lon = loc.get("lon", 31.2357)
        st.session_state.driver_lat = lat
        st.session_state.driver_lon = lon
    else:
        lat = st.session_state.get("driver_lat", 30.0444)
        lon = st.session_state.get("driver_lon", 31.2357)
        
except ImportError:
    # لو المكتبة مش متثبتة، استخدم الافتراضي
    lat = st.session_state.get("driver_lat", 30.0444)
    lon = st.session_state.get("driver_lon", 31.2357)

# حفظ الموقع مع رقمك واسمك اللي سجلت بيه
if db is not None:
    try:
        doc_id = DRIVER_PHONE.strip().replace("+", "")
        db.collection("users").document(doc_id).set({
            "last_location": {"lat": float(lat), "lon": float(lon)},
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "is_online": True,
            "driver_name": DRIVER_NAME,
            "driver_phone": DRIVER_PHONE,
            "driver_role": worker_role
        }, merge=True)
        st.sidebar.success(f"📍 موقعك Live: {lat:.4f}, {lon:.4f}")
        st.sidebar.map([{"lat": float(lat), "lon": float(lon)}])
    except Exception as e:
        logger.error(f"GPS update failed: {e}")

# --- 3️⃣ رادار فحص قائمة الحظر الفورية منع الاحتيال ---
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

# Live Order Radar
st.markdown("### 🔴 Live Order Radar - الطلبيات اللحظية")
col_radar1, col_radar2 = st.columns([3, 1])
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
                budget = o.get("customer_budget", o.get("suggested_price", "---"))

                badge_color = "#D97706" if is_courier else "#2563EB"
                st.markdown(f"""
                <div style='background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-right: 5px solid {badge_color}; margin-bottom: 10px; text-align: right;'>
                    <b style='color: #111827;'>📍 طلب مباشر من: {html_mod.escape(str(client_name))}</b><br>
                    <span style='color: #4B5563;'>📦 نوع الخدمة: {html_mod.escape(str(details))}</span><br>
                    <b style='color: #10B981;'>💵 ميزانية العميل: {html_mod.escape(str(budget))} جنيه</b>
                </div>
                """, unsafe_allow_html=True)

                bid_key = f"live_bid_input_{o_id}"
                bid_amount = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=5, value=int(budget) if isinstance(budget, (int, float)) else 20, key=bid_key)

                if st.button("🚀 إرسال عرض مباشر للطلب", key=f"live_bid_submit_{o_id}"):
                    try:
                        if not db:
                            st.error("قاعدة البيانات غير متصلة حالياً — لا يمكن إرسال العرض.")
                        else:
                            current = doc.to_dict() or {}
                            bids = current.get("bids", []) or []
                            new_bid = {
                                "driver_name": DRIVER_NAME,
                                "driver_id": DRIVER_PHONE,
                                "bid_amount": float(bid_amount),
                                "timestamp": datetime.now().isoformat(),
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

col_metric1, col_metric2 = st.columns(2)
with col_metric1:
    metric_label = "📦 الطرود الموصلة" if is_courier else "📊 الرحلات المكتملة"
    st.metric(label=metric_label, value="3,536 مهمة")
with col_metric2:
    st.metric(label="💰 إجمالي الإيرادات", value="340,904.74 ج.م")

st.markdown("---")

current_balance = -160.96

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

# 📥 التبويب الأول
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

# 📍 التبويب الثاني
with driver_tabs[1]:
    st.markdown("#### 📍 شاشة التنفيذ وتتبع المهمة الحالية")
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
                    <p style='margin: 8px 0;'><b>📦 التفاصيل:</b> {html_mod.escape(str(m_data.get('order_type', '')))} - {html_mod.escape(str(m_data.get('pickup_location', '')))} ← {html_mod.escape(str(m_data.get('destination_location', '')))}</p>
                    <hr style='border-color: #374151;'>
                    <b style='color: #FBBF24; font-size: 16px;'>💰 القيمة المتفق عليها: {m_data.get('final_price') or m_data.get('customer_budget')}.00 جنيه</b><br>
                    <small style='color: #9CA3AF;'>🚨 حالة المهمة الحية: {status}</small>
                </div>
                """, unsafe_allow_html=True)

                if status == "bid_accepted":
                    if st.button("📦 تم الاستلام من المرسل/الموكل", key=f"btn_picked_{m_id}"):
                        try:
                            if firestore:
                                db.collection("order_lifecycles").document(m_id).update({"status": "picked_up", "picked_up_at": firestore.SERVER_TIMESTAMP})
                            else:
                                db.collection("order_lifecycles").document(m_id).update({"status": "picked_up"})
                            st.success("🔔 تم تأكيد الاستلام. انتقل الطلب إلى حالة 'PICKED_UP'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل تحديث الحالة: {e}")
                elif status == "picked_up":
                    if st.button("🚴 في الطريق للعميل - بدء التتبع", key=f"btn_transit_{m_id}"):
                        try:
                            if firestore:
                                db.collection("order_lifecycles").document(m_id).update({"status": "in_transit", "in_transit_at": firestore.SERVER_TIMESTAMP})
                            else:
                                db.collection("order_lifecycles").document(m_id).update({"status": "in_transit"})
                            st.success("🚚 تم تحديث الحالة إلى 'IN_TRANSIT'.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"فشل تحديث الحالة: {e}")
                elif status == "in_transit":
                    if st.button("✅ تم التوصيل وتسوية المبلغ", key=f"btn_delivered_{m_id}"):
                        try:
                            if firestore:
                                db.collection("order_lifecycles").document(m_id).update({"status": "delivered", "delivered_at": firestore.SERVER_TIMESTAMP})
                            else:
                                db.collection("order_lifecycles").document(m_id).update({"status": "delivered"})
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

# 💳 التبويب الثالث
with driver_tabs[2]:
    st.markdown("#### 💳 المحفظة والشحن الإلكتروني عبر Paymob")
    st.write(f"رصيدك الحالي: **{current_balance:.2f} ج.م**")
    if current_balance < 0:
        st.error(f"⚠️ يوجد عليك مديونية متأخرة بقيمة {abs(current_balance):.2f} ج.م. يرجى الشحن لتفادي تجميد الحساب.")
    
    topup_amount = st.number_input("حدد مبلغ الشحن لتسديد المديونية أو شحن الرصيد (ج.م):", min_value=10, value=200, step=10)
    
    if st.button("💳 بدء عملية الدفع والشحن عبر Paymob", use_container_width=True):
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
            try:
                integration_id = st.secrets.get("paymob", {}).get("PAYMOB_INTEGRATION_ID")
                iframe_id = st.secrets.get("paymob", {}).get("PAYMOB_IFRAME_ID")

                auth_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": paymob_api_key}, timeout=15)
                auth_res.raise_for_status()
                auth_token = auth_res.json().get("token")
                if not auth_token:
                    st.error("تعذر الحصول على توكن المصادقة من Paymob.")
                else:
                    order_payload = {
                        "auth_token": auth_token,
                        "delivery_needed": "false",
                        "amount_cents": str(int(topup_amount * 100)),
                        "currency": "EGP",
                        "merchant_order_id": f"TOPUP-{user_data.get('role', 'driver').upper()}-{int(time.time())}"
                    }
                    order_res = requests.post("https://accept.paymob.com/api/ecommerce/orders", json=order_payload, timeout=15)
                    order_res.raise_for_status()
                    order_id = order_res.json().get("id")

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

                    payment_key_res = requests.post("https://accept.paymob.com/api/acceptance/payment_keys", json=payment_key_payload, timeout=15)
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
    st.markdown("#### 🛡️ بوابة توثيق السائقين والمناديب (KYC)")
    st.info("يرجى إرفاق صور المستندات الرسمية (الوجه الأمامي والخلفي للبطاقة والرخصة والمركبة) لتفعيل الحساب.")

    with st.form("driver_kyc_form"):
        col1, col2 = st.columns(2)
        with col1:
            national_id = st.text_input("🆔 الرقم القومي (14 رقماً):", key="national_id_input")
            email = st.text_input("📧 البريد الإلكتروني الفعال:", key="driver_email_input")
        with col2:
            drv_license = st.text_input("🚗 رقم رخصة القيادة:", key="driver_license_number")
            veh_license = st.text_input("🚙 رقم رخصة المركبة / اللوحة:", key="vehicle_license_number")

        st.markdown("#### 📎 رفع المستندات الرسمية (6 صور)")
        col_files1, col_files2, col_files3 = st.columns(3)
        
        with col_files1:
            front_id = st.file_uploader("📷 صورة البطاقة (وش)", type=["jpg", "jpeg", "png", "pdf"], key="front_id_upload")
            vehicle_front = st.file_uploader("🚗 صورة المركبة (وش)", type=["jpg", "jpeg", "png", "pdf"], key="vehicle_front_upload")
        
        with col_files2:
            back_id = st.file_uploader("📷 صورة البطاقة (ظهر)", type=["jpg", "jpeg", "png", "pdf"], key="back_id_upload")
            vehicle_back = st.file_uploader("🚗 صورة المركبة (ظهر)", type=["jpg", "jpeg", "png", "pdf"], key="vehicle_back_upload")
        
        with col_files3:
            license_front = st.file_uploader("📄 صورة الرخصة (وش)", type=["jpg", "jpeg", "png", "pdf"], key="license_front_upload")
            license_back = st.file_uploader("📄 صورة الرخصة (ظهر)", type=["jpg", "jpeg", "png", "pdf"], key="license_back_upload")

        if st.form_submit_button("🚀 إرسال المستندات والموقع للاعتماد", key="submit_kyc_form", use_container_width=True):
            if not national_id or not drv_license:
                st.warning("⚠️ يرجى تعبئة الحقول الأساسية (الرقم القومي ورخصة القيادة).")
            else:
                uploaded_files = {
                    "front_id": front_id,
                    "back_id": back_id,
                    "vehicle_front": vehicle_front,
                    "vehicle_back": vehicle_back,
                    "license_front": license_front,
                    "license_back": license_back,
                }
                
                result = upload_driver_docs(
                    driver_phone=DRIVER_PHONE,
                    driver_name=DRIVER_NAME,
                    uploaded_files=uploaded_files,
                    db=db,
                )
                
                if result["success"]:
                    try:
                        doc_id = DRIVER_PHONE.strip().replace("+", "")
                        db.collection("users").document(doc_id).set({
                            "national_id": national_id,
                            "email": email,
                            "driving_license": drv_license,
                            "vehicle_license": veh_license,
                            "kyc_status": "قيد المراجعة",
                            "kyc_type": "driver",
                            "documents": result["urls"],
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }, merge=True)
                    except Exception as e:
                        logger.error("Failed to update Firestore after document upload: %s", e)
                
                st.success(result["message"])

    st.markdown("---")
    st.markdown("#### 🛠️ مركز المساعدة والدعم المباشر")
    st.caption("تواصل مع غرفة عمليات منصة منجز للإبلاغ عن مشاكل الميدان أو توثيق الرحلات الكاش.")
