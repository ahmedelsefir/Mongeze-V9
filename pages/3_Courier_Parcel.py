import streamlit as st
import pandas as pd
from firebase_helpers import fetch_from_firebase, update_firebase_node
from firebase_helpers import sanitize_username, get_current_timestamp

st.set_page_config(page_title="📦 رادار مرسول الطرود والتوصيل", layout="wide")

st.title("📦 رادار مرسول الطرود والتوصيل")
st.markdown("---")

# جلب الطلبيات من نود 'deliveries'
try:
    deliveries = fetch_from_firebase("deliveries")
except Exception as e:
    st.error(f"خطأ في جلب بيانات الطرود: {e}")
    deliveries = None

rows = []
if deliveries:
    if isinstance(deliveries, dict):
        items = deliveries.items()
    elif isinstance(deliveries, list):
        items = enumerate(deliveries)
    else:
        items = []

    for key, d in items:
        try:
            item = d or {}
            parcel = item.get("parcel_description") or item.get("order_details") or "بند عام"
            pickup = item.get("pickup_address") or item.get("pickup") or "N/A"
            dropoff = item.get("dropoff_address") or item.get("dropoff") or "N/A"
            suggested = item.get("suggested_price") or item.get("budget") or "---"
            status = item.get("status") or "pending"

            rows.append({
                "delivery_id": key,
                "parcel": parcel,
                "pickup": pickup,
                "dropoff": dropoff,
                "suggested_price": suggested,
                "status": status,
            })
        except Exception:
            continue

if not rows:
    st.info("📭 لا توجد طلبيات تسليم متاحة حالياً.")
else:
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("تفاصيل الطرد وخيارات العرض")

    for d in rows:
        did = d["delivery_id"]
        with st.expander(f"📦 {d['parcel']} — {d['pickup']} → {d['dropoff']}"):
            st.write(f"- وصف الطرد: **{d['parcel']}**")
            st.write(f"- موقع الاستلام: **{d['pickup']}**")
            st.write(f"- موقع التسليم: **{d['dropoff']}**")
            st.write(f"- السعر المقترح من العميل: **{d['suggested_price']}**")
            st.write(f"- حالة الطلب: **{d['status']}**")

            bid = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=5, value=int(d.get('suggested_price') if isinstance(d.get('suggested_price'), (int, float)) else 50), key=f"bid_input_{did}")
            if st.button("🚀 إرسال عرض التسليم", key=f"send_bid_{did}"):
                try:
                    bidder = sanitize_username(st.session_state.get("user_name", "unknown"))
                    bid_data = {"bid": float(bid), "by": bidder, "ts": get_current_timestamp()}
                    update_firebase_node(f"deliveries/{did}/bids/{bidder}", bid_data)
                    st.success("🟢 تم إرسال عرضك بنجاح. بانتظار مقارنة العروض والموافقة من العميل.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"فشل إرسال العرض: {e}")
