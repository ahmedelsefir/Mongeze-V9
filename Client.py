"""
Client.py - Customer-facing views for the Monjez platform.
Contains: Parcels, Taxi, Customer Chat, and Customer Tracking views.
All views are imported and rendered from main.py.
"""

import streamlit as st
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


def render_parcels_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert):
    """Render the parcels ordering page for customers."""
    st.markdown("## 📦 مركز بث طلبات الطرود والشحن التجاري")
    with st.form("parcel_v10"):
        details = st.text_area("تفاصيل الشحنة وعنوان الالتقاط والتوصيل بدقة:")
        price = st.number_input("الميزانية المقترحة (ج.م):", min_value=10.0, value=70.0)
        if st.form_submit_button("🚀 بث الطلب فوراً للشبكة") and details.strip():
            try:
                order_id = f"PRCL-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "طرد تكميلي", "customer": user_name,
                    "details": details.strip(), "price": price, "status": "جاري البحث عن كابتن",
                    "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"طلب طرد جديد {order_id}", f"العميل {user_name} طلب توصيل طرد بقيمة {price} ج.م")
                    st.success(f"🎉 تم بث الطلب بنجاح! كود التتبع الفريد هو: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ فشل بث الطلب. تحقق من الاتصال.")
            except Exception as e:
                logger.error(f"Error creating parcel order: {str(e)}")
                st.error(f"حدث خطأ: {str(e)}")


def render_taxi_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert):
    """Render the taxi ordering page for customers."""
    st.markdown("## 🚕 مركز طلبات توصيل التاكسي والأفراد")
    with st.form("taxi_v10"):
        start = st.text_input("نقطة الانطلاق (منين؟):")
        end = st.text_input("الوجهة المراد الوصول إليها (على فين؟):")
        price = st.number_input("عرض السعر المقترح للرحلة:", min_value=20.0, value=120.0)
        if st.form_submit_button("🚕 بث الرحلة فوراً لايف") and start.strip() and end.strip():
            try:
                order_id = f"TAXI-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "تاكسي أفراد", "customer": user_name,
                    "from": start.strip(), "to": end.strip(), "price": price, "status": "جاري البحث عن كابتن",
                    "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"طلب تاكسي جديد {order_id}", f"الراكب {user_name} اطلب رحلة من {start} إلى {end}")
                    st.success(f"🎉 تم بث الرحلة بنجاح! كود التتبع: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ فشل بث الرحلة. تحقق من الاتصال.")
            except Exception as e:
                logger.error(f"Error creating taxi order: {str(e)}")
                st.error(f"حدث خطأ: {str(e)}")


def render_chat_page(user_name, user_role, send_to_firebase, fetch_from_firebase):
    """Render the chat rooms page."""
    st.markdown("## 💬 غرف المحادثة والاتصال اللحظي الموحد (نظام واتساب)")
    try:
        orders = fetch_from_firebase("orders")
        room_options = ["الشات العام للإدارة والموظفين"]
        if orders:
            for o in orders:
                try:
                    room_options.append(f"محادثة طلب {o.get('order_id', 'unknown')} - العميل: {o.get('customer', 'unknown')}")
                except Exception as option_error:
                    logger.warning(f"Error building room option: {str(option_error)}")
                    continue

        selected_room = st.selectbox("🎯 اختر قناة أو غرفة المحادثة النشطة لمتابعتها وتحديثها:", room_options)
        clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")

        with st.form("chat_form_v10", clear_on_submit=True):
            msg_text = st.text_input("📝 اكتب رسالتك اللحظية هنا:")
            if st.form_submit_button("💬 إرسال وبث") and msg_text.strip():
                try:
                    send_to_firebase(f"private_chats/{clean_room}", {
                        "role": user_role, "sender": user_name, "message": msg_text.strip(),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    time.sleep(0.2)
                except Exception as chat_error:
                    logger.error(f"Error sending chat message: {str(chat_error)}")
                    st.error("❌ فشل إرسال الرسالة")

        # سحب وعرض الرسائل الحية للغرفة المحددة من الأحدث للأقدم
        try:
            chats = fetch_from_firebase(f"private_chats/{clean_room}")
            if chats and len(chats) > 0:
                for m in chats[-20:]:
                    try:
                        role_color = "#1E88E5" if m.get("role") == "إدارة وموظفين" else "#2ECC71" if m.get("role") == "عميل" else "#F1C40F"
                        st.markdown(f"""
                        <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 6px; border-right: 5px solid {role_color}; text-align: right;'>
                            <span style='color: {role_color}; font-weight: bold;'>[{m.get('role', 'Unknown')}] {m.get('sender', 'Unknown')}</span> 
                            <span style='font-size: 0.75em; color: gray;'>({m.get('timestamp', '')})</span>: 
                            <p style='margin-top: 4px; font-size: 1.1em; color: black;'>{m.get('message', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as msg_error:
                        logger.warning(f"Error rendering message: {str(msg_error)}")
                        continue
        except Exception as chat_fetch_error:
            logger.error(f"Error fetching chat messages: {str(chat_fetch_error)}")
            st.warning("⚠️ خطأ في جلب الرسائل")
    except Exception as e:
        logger.error(f"Error in chat page: {str(e)}")
        st.error("حدث خطأ في صفحة الدردشة")


def render_customer_tracking(fetch_from_firebase, get_live_distance_for_order, format_distance_display):
    """Render customer order tracking view."""
    st.subheader("🕵️‍♂️ مراقبة حالة طلبك الحالي:")
    orders = fetch_from_firebase("orders")
    my_order = None
    if orders and st.session_state.get("my_active_order_id"):
        my_order = next((o for o in orders if o.get("order_id") == st.session_state["my_active_order_id"]), None)

    if my_order:
        st.info(f"🔢 رقم الطلب الحالي: {my_order.get('order_id')} | الحالة الجارية: **{my_order.get('status')}**")
        if my_order.get("status") == "الكابتن في الطريق إليك":
            st.success(f"⚡ إشعار لايف: الكابتن ({my_order.get('driver')}) قبل طلبك وهو في طريقه لموقعك الآن!")
            distance = get_live_distance_for_order(my_order)
            distance_text = format_distance_display(distance)
            st.metric(label="المسافة الحية بينك وبين السائق", value=distance_text)
        st.metric(label="الفاتورة والحساب الجاري", value=f"{my_order.get('price')} ج.م")
    else:
        st.warning("📭 لا يوجد طلب نشط تحت التتبع حالياً لك. اذهب للأعلى وانشئ طرد أو تاكسي.")
