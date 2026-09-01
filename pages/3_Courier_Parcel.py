import streamlit as st
import pandas as pd
from firebase_helpers import fetch_from_firebase, update_firebase_node
from firebase_helpers import sanitize_username, get_current_timestamp
from firebase_helpers import init_firestore

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

# init db (used alongside fetch_from_firebase/update_firebase_node)
db = init_firestore()

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

    # Live Order Tracker for selected delivery
    st.markdown("---")
    st.markdown("### 🔴 Live Order Tracker")
    delivery_ids = [r['delivery_id'] for r in rows]
    selected = st.selectbox("اختر طلباً لمتابعته لحظياً:", options=delivery_ids, key="select_live_delivery") if delivery_ids else None

    if selected:
        # fetch latest from firebase
        try:
            node = fetch_from_firebase(f"deliveries/{selected}")
        except Exception as e:
            st.error(f"فشل جلب بيانات الطلب: {e}")
            node = None

        if node:
            status = node.get('status', 'pending')
            color = "#F59E0B" if status=='pending' else ("#10B981" if status in ['picked_up','in_transit'] else ("#2563EB" if status=='bid_accepted' else "#6B7280"))
            st.markdown(f"<div style='padding:12px; border-radius:8px; background:{color}; color:white; text-align:right;'><b>حالة الطلب: {status.upper()}</b></div>", unsafe_allow_html=True)

            # show bids
            bids = node.get('bids', {}) if isinstance(node.get('bids', {}), dict) else node.get('bids', [])
            if not bids:
                st.info("لا توجد عروض حتى الآن.")
            else:
                st.markdown("#### العروض المقدمة")
                # bids may be dict keyed by bidder
                if isinstance(bids, dict):
                    for k, v in bids.items():
                        driver = v.get('by', k)
                        amount = v.get('bid', v.get('bid_amount', '-'))
                        st.write(f"- {driver}: {amount} ج.م")
                        if st.button("قبول العرض", key=f"accept_delivery_{selected}_{k}"):
                            try:
                                update_firebase_node(f"deliveries/{selected}", {"accepted_bid": {"by": driver, "amount": amount}, "status": "bid_accepted"})
                                st.success("✅ تم قبول العرض وسيتم إشعار المندوب.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"فشل قبول العرض: {e}")
                else:
                    for idx, b in enumerate(bids):
                        driver = b.get('driver_name', b.get('by', 'غير معروف'))
                        amount = b.get('bid_amount', b.get('bid', '-'))
                        st.write(f"- {driver}: {amount} ج.م")
                        if st.button("قبول العرض", key=f"accept_delivery_{selected}_{idx}"):
                            try:
                                update_firebase_node(f"deliveries/{selected}", {"accepted_bid": {"by": driver, "amount": amount}, "status": "bid_accepted"})
                                st.success("✅ تم قبول العرض وسيتم إشعار المندوب.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"فشل قبول العرض: {e}")

    # existing rows listing with bid submission
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
