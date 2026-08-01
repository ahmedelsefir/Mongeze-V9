import streamlit as st
import pandas as pd
import requests
import time
from firebase_helpers import fetch_from_firebase, update_firebase_node
from firebase_helpers import sanitize_username, get_current_timestamp

st.set_page_config(page_title="🚖 رادار كابتن التاكسي والملاكي", layout="wide")

st.title("🚖 رادار كابتن التاكسي والملاكي")
st.markdown("---")

# جلب الرحلات النشطة من نود 'rides'
try:
    rides = fetch_from_firebase("rides")
except Exception as e:
    st.error(f"خطأ في جلب بيانات الرحلات: {e}")
    rides = None

rows = []
if rides:
    # دعم صيغ البيانات: dict أو list
    if isinstance(rides, dict):
        items = rides.items()
    elif isinstance(rides, list):
        items = enumerate(rides)
    else:
        items = []

    for key, ride in items:
        try:
            r = ride or {}
            passenger = r.get("passenger_name") or r.get("client_name") or r.get("customer_name") or "غير معروف"
            pickup = r.get("pickup_address") or r.get("pickup") or "N/A"
            dropoff = r.get("dropoff_address") or r.get("dropoff") or "N/A"
            distance = r.get("distance_km") or r.get("distance") or None
            fare = r.get("fare") or r.get("suggested_price") or "---"
            status = r.get("status") or "pending"

            rows.append({
                "ride_id": key,
                "passenger": passenger,
                "pickup": pickup,
                "dropoff": dropoff,
                "distance_km": distance,
                "fare": fare,
                "status": status,
            })
        except Exception:
            continue

if not rows:
    st.info("📭 لا توجد رحلات نشطة في الوقت الحالي.")
else:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("تفاصيل الرحلات وعمليات القبول")

    for r in rows:
        rid = r["ride_id"]
        with st.expander(f"🔎 {r['passenger']} — {r['pickup']} → {r['dropoff']}"):
            st.write(f"- اسم الراكب: **{r['passenger']}**")
            st.write(f"- نقطة الانطلاق: **{r['pickup']}**")
            st.write(f"- نقطة الوصول: **{r['dropoff']}**")
            st.write(f"- المسافة: **{r['distance_km']}**")
            st.write(f"- الأجرة المتوقعة: **{r['fare']}**")
            st.write(f"- حالة الرحلة: **{r['status']}**")

            if st.button("🚗 قبول الرحلة", key=f"accept_ride_{rid}"):
                try:
                    driver_name = st.session_state.get("user_name", "مستخدم")
                    update_firebase_node(f"rides/{rid}", {"status": "accepted", "driver": driver_name, "accepted_at": get_current_timestamp()})
                    st.success("✅ تم قبول الرحلة وتم تحديث الحالة في النظام")
                    st.rerun()
                except Exception as e:
                    st.error(f"فشل تحديث الرحلة: {e}")

# ---------------------------------------------------------
# 🚖 قسم محفظة السائق - محسّن مع Popover
# ---------------------------------------------------------
st.markdown("---")
st.subheader("💳 محفظة رصيد السائق")

# Fetch driver balance
driver_balance = 0.0
driver_name = st.session_state.get("user_name", "مستخدم")
try:
    driver_data = fetch_from_firebase(f"drivers/{sanitize_username(driver_name)}")
    if driver_data and isinstance(driver_data, dict):
        driver_balance = float(driver_data.get("wallet_balance", 0.0))
except Exception:
    driver_balance = 0.0

# Clean layout: Balance card with popover button
col_bal, col_btn = st.columns([3, 1])

with col_bal:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 20px; border-radius: 12px; margin-bottom: 16px;'>
        <p style='margin: 0; font-size: 14px; opacity: 0.9;'>رصيد الحساب الحالي</p>
        <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: bold;'>{driver_balance:.2f} ج.م</p>
    </div>
    """, unsafe_allow_html=True)

with col_btn:
    with st.popover("➕ إضافة", use_container_width=True):
        st.subheader("💳 أضف رصيد للمحفظة")
        st.caption("طريقة الدفع: بطاقة أئتمان / خصم عبر Paymob")
        
        topup_amount = st.number_input(
            "أدخل المبلغ المراد إضافته إلى رصيدك (جنيه)",
            min_value=10,
            max_value=50000,
            value=100,
            step=10,
            key="driver_topup_amount"
        )
        
        if st.button("دفع", type="primary", use_container_width=True, key="driver_topup_btn"):
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
                
                # 3. إنشاء طلب جديد (Order)
                order_res = requests.post(
                    "https://accept.paymob.com/api/ecommerce/orders",
                    json={
                        "auth_token": auth_token,
                        "delivery_needed": "false",
                        "amount_cents": str(int(topup_amount * 100)),
                        "currency": "EGP",
                        "merchant_order_id": f"TOPUP-DRIVER-{driver_name}-{int(time.time())}"
                    }
                )
                order_res.raise_for_status()
                paymob_order_id = order_res.json().get("id")
                
                st.success(f"✅ تم تحضير الدفع بنجاح — المبلغ: {topup_amount} ج.م")
                st.info(f"🆔 رقم المعاملة: `{paymob_order_id}`")
                
            except KeyError:
                st.error("❌ لم يتم العثور على مفاتيح Paymob! تأكد من حفظ قسم [paymob] في secrets.toml")
            except Exception as e:
                st.error(f"❌ خطأ في الاتصال بـ Paymob: {e}")
