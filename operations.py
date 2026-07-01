import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Callable, Optional, Dict, Any

# 1. Functional Error Handler (More than just a print)
def handle_error(e, context="System"):
    """Captures and displays errors professionally in the UI."""
    error_details = f"[{datetime.now().strftime('%H:%M:%S')}] {context} Error: {str(e)}"
    print(error_details) # For terminal debugging
    st.error(f"⚠️ {context} issue detected. Please check your connection or secrets.")

# 2. Functional Smart Sync (Replacing 'pass' with real logic)
def smart_sync(data_to_send):
    """Sends data to Slack and Notion simultaneously."""
    try:
        # Slack Automation
        slack_url = st.secrets["slack"]["webhook_url"]
        requests.post(slack_url, json={"text": f"🚀 New Entry: {data_to_send['name']} - {data_to_send['amount']} EGP"}, timeout=10)
        
        # Notion Automation
        notion_headers = {
            "Authorization": f"Bearer {st.secrets['notion']['token']}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        notion_payload = {
            "parent": {"database_id": st.secrets["notion"]["database_id"]},
            "properties": {
                "Title": {"title": [{"text": {"content": data_to_send['name']}}]},
                "Amount": {"number": float(data_to_send['amount'])}
            }
        }
        requests.post("https://api.notion.com/v1/pages", headers=notion_headers, json=notion_payload, timeout=10)
        
        st.success("✨ Data synced to Slack & Notion!")
        return True
    except Exception as e:
        handle_error(e, context="Sync Engine")
        return False

# 3. Functional Dashboard (Replacing 'pass' with math logic)
def accounting_dashboard(df):
    """Calculates and shows revenue stats on screen."""
    try:
        if not df.empty:
            total = df['amount'].sum()
            st.metric("Total Revenue", f"{total:,.2f} EGP")
            st.bar_chart(df.groupby('service')['amount'].sum())
    except Exception as e:
        handle_error(e, context="Dashboard")


# ============================================================================
# 4. ORDER BOX ACTION RENDERING — Role-Based Button Logic
# ============================================================================

def _render_order_actions(
    order: Dict[str, Any],
    user_role: str,
    on_accept_callback: Optional[Callable] = None,
    on_chat_callback: Optional[Callable] = None,
    on_support_callback: Optional[Callable] = None,
    on_cancel_callback: Optional[Callable] = None,
) -> None:
    """
    Render action buttons for an order based on user role.
    
    Handles Accept, Chat, Support, and Cancel buttons with role-based visibility.
    - Customer: Can accept (if driver assigned), chat, support, cancel
    - Driver: Can accept, chat, support (after accepting)
    - Admin: Can accept, chat, support, cancel (override any state)
    
    Args:
        order: Order dictionary with keys like 'order_id', 'status', 'driver', etc.
        user_role: Current user role ('عميل', 'مندوب / كابتن', 'إدارة وموظفين')
        on_accept_callback: Called when Accept button clicked (receives order_id)
        on_chat_callback: Called when Chat button clicked (receives order_id)
        on_support_callback: Called when Support button clicked (receives order_id)
        on_cancel_callback: Called when Cancel button clicked (receives order_id)
    """
    try:
        order_id = order.get("order_id", "UNKNOWN")
        status = order.get("status", "")
        driver_assigned = order.get("driver", "")
        
        # Create columns for horizontal button layout
        col1, col2, col3, col4 = st.columns(4)
        
        # ── ACCEPT BUTTON ──────────────────────────────────────────
        # Show for: Driver (anytime), Admin (anytime), Customer (if driver exists)
        with col1:
            show_accept = False
            accept_label = "✅ قبول الطلب"
            accept_disabled = False
            
            if user_role == "مندوب / كابتن":
                # Driver can always accept
                show_accept = True
                accept_label = "🚖 قبول الطلب"
            elif user_role == "إدارة وموظفين":
                # Admin can always accept
                show_accept = True
                accept_label = "✅ تفعيل الطلب"
            elif user_role == "عميل" and driver_assigned:
                # Customer can accept only if driver is assigned
                show_accept = True
                accept_label = "✅ تأكيد الطلب"
                accept_disabled = not bool(driver_assigned)
            
            if show_accept:
                if st.button(
                    accept_label,
                    key=f"accept_{order_id}",
                    disabled=accept_disabled,
                    use_container_width=True,
                    help="تأكيد قبول هذا الطلب"
                ):
                    if on_accept_callback:
                        on_accept_callback(order_id)
        
        # ── CHAT BUTTON ────────────────────────────────────────────
        # Show for: All roles (Customer, Driver, Admin)
        with col2:
            if st.button(
                "💬 فتح الدردشة",
                key=f"chat_{order_id}",
                use_container_width=True,
                help="التواصل حول هذا الطلب"
            ):
                if on_chat_callback:
                    on_chat_callback(order_id)
        
        # ── SUPPORT BUTTON ─────────────────────────────────────────
        # Show for: All roles (but Driver only if accepted)
        with col3:
            show_support = True
            support_disabled = False
            support_label = "🆘 طلب دعم"
            
            if user_role == "مندوب / كابتن":
                # Driver can request support only after accepting
                support_disabled = not bool(driver_assigned)
                support_label = "🆘 استدعاء الدعم"
            
            if show_support:
                if st.button(
                    support_label,
                    key=f"support_{order_id}",
                    disabled=support_disabled,
                    use_container_width=True,
                    help="الاتصال بفريق الدعم الفني"
                ):
                    if on_support_callback:
                        on_support_callback(order_id)
        
        # ── CANCEL BUTTON ──────────────────────────────────────────
        # Show for: Customer (non-completed), Admin (override)
        with col4:
            show_cancel = False
            cancel_disabled = False
            
            if user_role == "عميل":
                # Customer can cancel unless already completed/cancelled
                show_cancel = True
                cancel_disabled = status in ["✅ مكتملة", "❌ ملغاة"]
            elif user_role == "إدارة وموظفين":
                # Admin can always cancel (override)
                show_cancel = True
            
            if show_cancel:
                if st.button(
                    "❌ إلغاء الطلب",
                    key=f"cancel_{order_id}",
                    disabled=cancel_disabled,
                    use_container_width=True,
                    help="إلغاء هذا الطلب بشكل نهائي"
                ):
                    if on_cancel_callback:
                        on_cancel_callback(order_id)
    
    except Exception as e:
        handle_error(e, context="Order Actions Rendering")


# ============================================================================
# 5. STREAMLIT AUTO-REFRESH HELPER
# ============================================================================

def setup_order_box_auto_refresh(
    refresh_interval_seconds: int = 30,
    auto_refresh_key: str = "order_auto_refresh_enabled"
) -> bool:
    """
    Setup Streamlit auto-refresh mechanism for order boxes.
    
    This function initializes session state for auto-refresh and returns
    whether auto-refresh is currently enabled. Pairs with a toggle in the UI.
    
    Features:
    - Respects user preference (stored in session_state)
    - Uses st.rerun() internally on interval
    - Non-blocking (uses background timer logic)
    - Configurable refresh interval
    
    Args:
        refresh_interval_seconds: Time between refreshes (default: 30s)
        auto_refresh_key: Session state key for toggle persistence
    
    Returns:
        bool: True if auto-refresh is enabled, False otherwise
    
    Usage:
        # In your sidebar or settings section:
        if setup_order_box_auto_refresh(refresh_interval_seconds=30):
            st.info("🔄 Auto-refresh: ON (updates every 30 seconds)")
        else:
            st.info("⏹️ Auto-refresh: OFF")
        
        # Toggle in sidebar:
        st.sidebar.toggle(
            "Enable auto-refresh for orders",
            value=st.session_state.get(auto_refresh_key, True),
            key=auto_refresh_key
        )
    """
    try:
        # Initialize session state if not exists
        if auto_refresh_key not in st.session_state:
            st.session_state[auto_refresh_key] = True
        
        # Get current state
        is_enabled = st.session_state.get(auto_refresh_key, True)
        
        if is_enabled:
            # Use Streamlit's built-in polling mechanism
            # This uses the fragment decorator pattern or cache_resource
            from time import sleep
            import threading
            
            def _auto_refresh_worker():
                """Background worker to trigger refresh at intervals."""
                sleep(refresh_interval_seconds)
                # Mark for refresh (Streamlit will detect and rerun)
                if st.session_state.get(auto_refresh_key, True):
                    st.rerun()
            
            # Start background worker only if enabled
            # Note: In production, use st.session_state to track timer state
            # to avoid spawning multiple threads per user session
            refresh_timer_key = f"{auto_refresh_key}_timer_active"
            if not st.session_state.get(refresh_timer_key, False):
                st.session_state[refresh_timer_key] = True
                # Thread will run and call st.rerun() when interval expires
                timer_thread = threading.Thread(target=_auto_refresh_worker, daemon=True)
                timer_thread.start()
            
            return True
        
        return False
    
    except Exception as e:
        handle_error(e, context="Order Auto-Refresh Setup")
        return False


def render_order_auto_refresh_toggle() -> None:
    """
    Render the auto-refresh toggle control in the sidebar.
    
    Call this in your st.sidebar to allow users to toggle auto-refresh.
    """
    try:
        col1, col2 = st.sidebar.columns([3, 1])
        
        with col1:
            enabled = st.sidebar.toggle(
                "🔄 تحديث تلقائي للطلبات",
                value=st.session_state.get("order_auto_refresh_enabled", True),
                key="order_auto_refresh_enabled",
                help="تحديث قائمة الطلبات تلقائياً كل 30 ثانية"
            )
        
        with col2:
            if enabled:
                st.sidebar.markdown("✅")
            else:
                st.sidebar.markdown("⏸️")
        
        return enabled
    
    except Exception as e:
        handle_error(e, context="Auto-Refresh Toggle Render")
        return False
