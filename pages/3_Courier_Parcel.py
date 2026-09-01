import streamlit as st
import pandas as pd
from firebase_helpers import fetch_from_firebase, update_firebase_node
from firebase_helpers import sanitize_username, get_current_timestamp

# Defensive import for payment hub
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub  # type: ignore
    except Exception:
        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً — يرجى تفعيل صفحة Payment_Hub أو إعداد الأسرار.")
            return None

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

    # Unified pay button to open payment hub for debts/topups
    if st.button("💳 فتح مركز الدفع لتسديد/شحن الرصيد", use_container_width=False):
        try:
            # Open unified hub with a generic amount (user can edit in hub)
            render_payment_hub(purpose="debt", default_amount=100)
        except Exception as e:
            st.error(f"تعذر فتح بوابة الدفع: {e}")

    for d in rows:
        did = d["delivery_id"]
        with st.expander(f"📦 {d['parcel']} — {d['pickup']} → {d['dropoff']}"):
            st.write(f"- وصف الطرد: **{d['parcel']}**")
            st.write(f"- موقع الاستلام: **{d['pickup']}**")
            st.write(f"- موقع التسليم: **{d['dropoff']}**")
            st.write(f"- السعر المقترح من العميل: **{d['suggested_price']}**")
            st.write(f"- حالة الطلب: **{d['status']}**")

            # Safe default for number_input
            try:
                suggested_val = d.get('suggested_price')
                default_bid = int(suggested_val) if isinstance(suggested_val, (int, float)) else 10
            except Exception:
                default_bid = 10

            bid = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=5, value=default_bid, key=f"bid_{did}")

            if st.button("🚀 إرسال عرض التسليم", key=f"send_bid_{did}"):
                try:
                    bidder = sanitize_username(st.session_state.get("user_name", "unknown"))
                    bid_data = {"bid": float(bid), "by": bidder, "ts": get_current_timestamp()}
                    try:
                        update_firebase_node(f"deliveries/{did}/bids/{bidder}", bid_data)
                        st.success("🟢 تم إرسال عرضك بنجاح. بانتظار مقارنة العروض والموافقة من العميل.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"فشل إرسال العرض إلى السيرفر: {e}")
                except Exception as e:
                    st.error(f"فشل تجهيز العرض: {e}")
