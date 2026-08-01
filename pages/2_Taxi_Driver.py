import streamlit as st
import pandas as pd
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
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"فشل تحديث الرحلة: {e}")
