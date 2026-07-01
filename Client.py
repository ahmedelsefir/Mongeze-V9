"""
Client.py - Customer-facing views for the Monjez platform.
Contains: Parcels, Taxi, Customer Chat, and Customer Tracking views.
All views are imported and rendered from main.py.
"""

import html
import streamlit as st
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


def render_parcels_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert):
    """Render the parcels ordering page for customers."""
    st.markdown("## 📦 Parcel Shipment Center")
    with st.form("parcel_v10"):
        details = st.text_area("Shipment Details & Pickup/Delivery Addresses:")
        price = st.number_input("Estimated Budget (EGP):", min_value=10.0, value=70.0)
        if st.form_submit_button("🚀 Post Order to Network") and details.strip():
            try:
                order_id = f"PRCL-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "Parcel Delivery", "customer": user_name,
                    "details": details.strip(), "price": price, "status": "Searching for Driver",
                    "driver": "Not Assigned", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"New Parcel Order {order_id}", f"Customer {user_name} requested parcel delivery worth EGP {price}")
                    st.success(f"🎉 Order posted successfully! Tracking Code: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ Failed to post order. Please check your connection.")
            except Exception as e:
                logger.error(f"Error creating parcel order: {str(e)}")
                st.error(f"Error: {str(e)}")


def render_taxi_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert):
    """Render the taxi ordering page for customers."""
    st.markdown("## 🚕 Taxi Ride Request Center")
    with st.form("taxi_v10"):
        start = st.text_input("Pickup Location:")
        end = st.text_input("Destination:")
        price = st.number_input("Estimated Fare (EGP):", min_value=20.0, value=120.0)
        if st.form_submit_button("🚕 Post Ride to Network") and start.strip() and end.strip():
            try:
                order_id = f"TAXI-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "Taxi Ride", "customer": user_name,
                    "from": start.strip(), "to": end.strip(), "price": price, "status": "Searching for Driver",
                    "driver": "Not Assigned", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"New Taxi Request {order_id}", f"Passenger {user_name} requested ride from {start} to {end}")
                    st.success(f"🎉 Ride posted successfully! Tracking Code: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ Failed to post ride. Please check your connection.")
            except Exception as e:
                logger.error(f"Error creating taxi order: {str(e)}")
                st.error(f"Error: {str(e)}")


def _extract_order_id_from_room(selected_room):
    """Extract order_id from room selection string like 'Order Chat TAXI-123456 - Customer: ...'."""
    try:
        if "Order Chat" in selected_room:
            part = selected_room.split("Order Chat")[1].strip()
            order_id = part.split(" - ")[0].strip()
            return order_id
    except Exception:
        pass
    return None


def _find_order_by_id(orders, order_id):
    """Find an order dict from the orders list by order_id."""
    if not orders or not order_id:
        return None
    for o in orders:
        if o.get("order_id") == order_id:
            return o
    return None


def render_chat_page(user_name, user_role, send_to_firebase, fetch_from_firebase,
                     update_firebase_node=None, log_accounting_entry=None,
                     fetch_firebase_raw=None):
    """Render the chat rooms page with three-dot menu for order actions.

    Args:
        user_name: The current user's display name.
        user_role: The current user's role (Customer, Driver, Admin).
        send_to_firebase: Callable to POST data to a Firebase node.
        fetch_from_firebase: Callable to GET data from a Firebase node.
        update_firebase_node: Callable to PATCH a Firebase node (for status updates).
        log_accounting_entry: Callable to log accounting ledger entries.
        fetch_firebase_raw: Callable to GET raw JSON from a Firebase node (flat objects).
    """
    st.markdown("## 💬 Live Chat & Unified Communication")
    try:
        orders = fetch_from_firebase("orders")
        room_options = ["Admin & Staff General Chat"]
        if orders:
            for o in orders:
                try:
                    room_options.append(f"Order Chat {o.get('order_id', 'unknown')} - Customer: {o.get('customer', 'unknown')}")
                except Exception as option_error:
                    logger.warning(f"Error building room option: {str(option_error)}")
                    continue

        selected_room = st.selectbox("🎯 Select Active Chat Channel:", room_options)
        clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")

        # Extract order_id from the selected room for contextual actions
        current_order_id = _extract_order_id_from_room(selected_room)
        current_order = _find_order_by_id(orders, current_order_id) if current_order_id else None
        is_order_room = current_order_id is not None

        # ── Three-Dot Menu (More Options) ──────────────────────────
        if is_order_room:
            _render_chat_actions_menu(
                user_name=user_name,
                user_role=user_role,
                order_id=current_order_id,
                order_data=current_order,
                clean_room=clean_room,
                send_to_firebase=send_to_firebase,
                fetch_from_firebase=fetch_from_firebase,
                update_firebase_node=update_firebase_node,
                log_accounting_entry=log_accounting_entry,
            )

        # ── Live Support Banner ────────────────────────────────────
        if is_order_room:
            _render_support_banner(current_order_id, fetch_firebase_raw)

        # ── Chat Message Input ─────────────────────────────────────
        with st.form("chat_form_v10", clear_on_submit=True):
            msg_text = st.text_input("📝 Type your message:")
            if st.form_submit_button("💬 Send Message") and msg_text.strip():
                try:
                    send_to_firebase(f"private_chats/{clean_room}", {
                        "role": user_role, "sender": user_name, "message": msg_text.strip(),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    time.sleep(0.2)
                except Exception as chat_error:
                    logger.error(f"Error sending chat message: {str(chat_error)}")
                    st.error("❌ Failed to send message")

        # ── Live Messages ──────────────────────────────────────────
        try:
            chats = fetch_from_firebase(f"private_chats/{clean_room}")
            if chats and len(chats) > 0:
                for m in chats[-20:]:
                    try:
                        role_color = "#1E88E5" if m.get("role") == "Admin" else "#2ECC71" if m.get("role") == "Customer" else "#F1C40F"
                        st.markdown(f"""
                        <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 6px; border-right: 5px solid {role_color};'>
                            <span style='color: {role_color}; font-weight: bold;'>[{html.escape(str(m.get('role', 'Unknown')))}] {html.escape(str(m.get('sender', 'Unknown')))}</span> 
                            <span style='font-size: 0.75em; color: gray;'>({html.escape(str(m.get('timestamp', '')))})</span>: 
                            <p style='margin-top: 4px; font-size: 1.1em; color: black;'>{html.escape(str(m.get('message', '')))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as msg_error:
                        logger.warning(f"Error rendering message: {str(msg_error)}")
                        continue
        except Exception as chat_fetch_error:
            logger.error(f"Error fetching chat messages: {str(chat_fetch_error)}")
            st.warning("⚠️ Error loading messages")
    except Exception as e:
        logger.error(f"Error in chat page: {str(e)}")
        st.error("Error loading chat page")


def _render_chat_actions_menu(user_name, user_role, order_id, order_data,
                              clean_room, send_to_firebase, fetch_from_firebase,
                              update_firebase_node, log_accounting_entry):
    """Render the three-dot contextual menu at the top of the chat box.

    Provides two actions:
    1. Cancel Order — prompts confirmation, updates Firebase status, closes chat, logs ledger.
    2. Get Support — opens a parallel support sub-channel tagging admin staff.
    """
    try:
        order_status = order_data.get("status", "") if order_data else ""
        is_cancelled = order_status == "Cancelled"

        with st.popover("⋮ More Options", use_container_width=False):
            st.markdown(f"**🔖 Order:** `{order_id}`")
            if order_status:
                st.caption(f"Current Status: {order_status}")
            st.divider()

            # ── Action 1: Cancel Order ─────────────────────────────
            st.markdown("##### ❌ Cancel Order")
            if is_cancelled:
                st.info("This order is already cancelled.")
            else:
                st.warning("⚠️ Are you sure you want to cancel this order? This action cannot be undone.")
                if st.button("🗑️ Confirm Cancellation", key="confirm_cancel_order",
                             type="primary", use_container_width=True):
                    _handle_cancel_order(
                        user_name=user_name,
                        user_role=user_role,
                        order_id=order_id,
                        order_data=order_data,
                        clean_room=clean_room,
                        send_to_firebase=send_to_firebase,
                        update_firebase_node=update_firebase_node,
                        log_accounting_entry=log_accounting_entry,
                    )

            st.divider()

            # ── Action 2: Get Support ──────────────────────────────
            st.markdown("##### 🚨 Request Support")
            st.caption("Opens an immediate support channel and notifies the admin team.")
            if st.button("📞 Call Support Now", key="request_support",
                         use_container_width=True):
                _handle_request_support(
                    user_name=user_name,
                    user_role=user_role,
                    order_id=order_id,
                    clean_room=clean_room,
                    send_to_firebase=send_to_firebase,
                    update_firebase_node=update_firebase_node,
                )
    except Exception as e:
        logger.error(f"Error rendering chat actions menu: {str(e)}")
        st.error("⚠️ Error loading options menu")


def _handle_cancel_order(user_name, user_role, order_id, order_data,
                         clean_room, send_to_firebase, update_firebase_node,
                         log_accounting_entry):
    """Process order cancellation: update Firebase, log ledger, close chat."""
    try:
        db_id = order_data.get("db_id") if order_data else None
        if not db_id:
            st.error("❌ Cannot find order data in database.")
            return

        # 1. Update order status to Cancelled in Firebase
        if update_firebase_node:
            success = update_firebase_node(f"orders/{db_id}", {
                "status": "Cancelled",
                "cancelled_by": user_name,
                "cancelled_role": user_role,
                "cancelled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            if not success:
                st.error("❌ Failed to update order status. Please try again.")
                return
        else:
            st.warning("⚠️ Database update service is currently unavailable.")
            return

        # 2. Log cancellation in the accounting ledger
        if log_accounting_entry:
            log_accounting_entry(order_id, {
                "event": "order_cancelled",
                "cancelled_by": user_name,
                "cancelled_role": user_role,
                "original_price": order_data.get("price", 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Cancelled from chat",
            })

        # 3. Post a system message in the chat room
        try:
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": "System",
                "sender": "⚙️ System",
                "message": f"❌ Order {order_id} has been cancelled by {user_name} ({user_role})",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post cancellation chat message: {str(msg_err)}")

        # 4. Clear active order tracking if this was the user's active order
        if st.session_state.get("my_active_order_id") == order_id:
            st.session_state["my_active_order_id"] = None

        st.success(f"Order {order_id} has been cancelled successfully.")
        st.info("🔄 Page will update automatically...")

    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {str(e)}")
        st.error(f"❌ Error cancelling order: {str(e)}")


def _handle_request_support(user_name, user_role, order_id, clean_room,
                            send_to_firebase, update_firebase_node):
    """Open a parallel support sub-channel inside chats/{order_id} and tag admin staff."""
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Create/update the support flag node under chats/{order_id}
        support_node = f"chats/{order_id}/support_request"
        support_data = {
            "active": True,
            "requested_by": user_name,
            "requested_role": user_role,
            "requested_at": now_str,
            "status": "awaiting_admin",
        }

        if update_firebase_node:
            success = update_firebase_node(support_node, support_data)
            if not success:
                st.error("❌ Failed to open support channel. Please try again.")
                return
        else:
            st.warning("⚠️ Database update service is currently unavailable.")
            return

        # 2. Post initial support message in the sub-channel
        support_chat_node = f"chats/{order_id}/support_messages"
        try:
            send_to_firebase(support_chat_node, {
                "role": "System",
                "sender": "🚨 Support System",
                "message": f"Support channel opened for Order {order_id} by {user_name}. Admin team will receive immediate notification.",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post initial support message: {str(msg_err)}")

        # 3. Post a notification message in the main chat room
        try:
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": "System",
                "sender": "🚨 Support System",
                "message": f"🚨 Support has been requested for Order {order_id} — Admin team is being notified.",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as msg_err:
            logger.warning(f"Failed to post support notification to chat: {str(msg_err)}")

        st.success("Support channel opened successfully! Admin team has been notified.")
        st.info("🔄 Support banner will appear at the top for all participants.")

    except Exception as e:
        logger.error(f"Error requesting support for order {order_id}: {str(e)}")
        st.error(f"❌ Error requesting support: {str(e)}")


def _render_support_banner(order_id, fetch_firebase_raw):
    """Show a live support banner if a support request is active for this order.

    Visible to all participants (customer, driver, admin) so everyone knows
    support staff have been tagged.
    """
    if not fetch_firebase_raw:
        return
    try:
        support_data = fetch_firebase_raw(f"chats/{order_id}/support_request")
        if not support_data or not isinstance(support_data, dict):
            return

        is_active = support_data.get("active", False)
        requester = support_data.get("requested_by", "")
        requested_at = support_data.get("requested_at", "")

        if is_active:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #ff4444, #cc0000); color: white;
                        padding: 12px 16px; border-radius: 10px; margin-bottom: 12px;'>
                <strong>🚨 Support Required</strong> — Admin team has been called for Order <code style='color: #ffcccc;'>{html.escape(str(order_id))}</code>
                <br><span style='font-size: 0.85em; opacity: 0.9;'>
                    Requested by: {html.escape(str(requester))} • {html.escape(str(requested_at))}
                </span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        logger.warning(f"Error checking support status for order {order_id}: {str(e)}")


def render_customer_tracking(fetch_from_firebase, get_live_distance_for_order, format_distance_display):
    """Render customer order tracking view."""
    st.subheader("🕵️‍♂️ Track Your Current Order:")
    orders = fetch_from_firebase("orders")
    my_order = None
    if orders and st.session_state.get("my_active_order_id"):
        my_order = next((o for o in orders if o.get("order_id") == st.session_state["my_active_order_id"]), None)

    if my_order:
        st.info(f"📦 Order ID: {my_order.get('order_id')} | Status: **{my_order.get('status')}**")
        if my_order.get("status") == "Driver En Route":
            st.success(f"⚡ Alert: Driver ({my_order.get('driver')}) has accepted your order and is on the way!")
            distance = get_live_distance_for_order(my_order)
            distance_text = format_distance_display(distance)
            st.metric(label="Live Distance to Driver", value=distance_text)
        st.metric(label="Fare Amount", value=f"EGP {my_order.get('price')}")
    else:
        st.warning("📭 No active order to track. Create a parcel or taxi order to get started.")
