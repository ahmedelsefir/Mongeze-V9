"""
Order Box Component (صندوق الطلبات)

A unified, reusable component for organizing, displaying, and tracking live order updates.
Supports real-time Firebase synchronization, multiple views (grid/list), and order actions.
Used across Client, Driver, and Admin dashboards.

Author: Mongeze Development Team
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ORDER BOX CORE COMPONENT
# ============================================================================

def render_order_box(
    order: Dict,
    user_role: str,
    on_accept_callback: Optional[Callable] = None,
    on_cancel_callback: Optional[Callable] = None,
    on_chat_callback: Optional[Callable] = None,
    on_support_callback: Optional[Callable] = None,
    compact_mode: bool = False
) -> None:
    """
    Render a single order box with professional styling and real-time status tracking.

    Args:
        order: Order dictionary from Firebase with keys: order_id, type, customer, 
               driver, status, price, details/from/to, timestamp
        user_role: Current user role (Customer, Driver, Admin)
        on_accept_callback: Callback function when driver accepts order
        on_cancel_callback: Callback function when order is cancelled
        on_chat_callback: Callback function to open chat
        on_support_callback: Callback function to request support
        compact_mode: If True, render minimal view; if False, full details

    Returns:
        None (renders directly to Streamlit)
    """
    try:
        # Extract order details with safe defaults
        order_id = order.get("order_id", "UNKNOWN")
        order_type = order.get("type", "Order")
        customer = order.get("customer", "Unknown Customer")
        driver = order.get("driver", "Not Assigned")
        status = order.get("status", "Pending")
        price = order.get("price", 0)
        timestamp = order.get("timestamp", "")
        
        # Get location details based on order type
        if order_type == "Parcel Delivery":
            location_details = f"📝 {order.get('details', 'No details provided')[:80]}"
        else:  # Taxi Ride
            from_loc = order.get("from", "Unknown")
            to_loc = order.get("to", "Unknown")
            location_details = f"📍 {from_loc} → {to_loc}"
        
        # Determine status color and icon
        status_config = _get_status_config(status)
        
        # Main order box container
        with st.container():
            # Create styled container with border
            if not compact_mode:
                st.markdown(
                    f"""
                    <div style='
                        border-left: 5px solid {status_config["color"]};
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 12px;
                    '>
                    """,
                    unsafe_allow_html=True
                )
            
            # Header: Order ID + Status
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.markdown(f"**{status_config['icon']} Order #{order_id}**")
            with col2:
                st.markdown(f"<span style='color: {status_config['color']}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)
            with col3:
                st.caption(f"🕐 {timestamp}")
            
            st.divider()
            
            # Details: Type, Customer, Driver
            detail_col1, detail_col2, detail_col3 = st.columns(3)
            with detail_col1:
                st.markdown(f"**Type:** {order_type}")
            with detail_col2:
                st.markdown(f"**Customer:** {customer}")
            with detail_col3:
                st.markdown(f"**Driver:** {driver}")
            
            # Location details
            st.markdown(location_details)
            
            # Fare/Price
            st.markdown(f"**💰 Fare:** EGP {price}")
            
            # Action buttons based on user role and order status
            _render_order_actions(
                order_id=order_id,
                status=status,
                user_role=user_role,
                order=order,
                on_accept_callback=on_accept_callback,
                on_cancel_callback=on_cancel_callback,
                on_chat_callback=on_chat_callback,
                on_support_callback=on_support_callback
            )
            
            if not compact_mode:
                st.markdown("</div>", unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Error rendering order box for {order.get('order_id', 'UNKNOWN')}: {str(e)}")
        st.error(f"Error displaying order: {str(e)}")


# ============================================================================
# ORDER BOX CONTAINER (GRID/LIST VIEW)
# ============================================================================

def render_order_box_container(
    orders: List[Dict],
    user_role: str,
    filter_status: Optional[str] = None,
    view_mode: str = "list",  # "list" or "grid"
    max_orders: Optional[int] = None,
    on_accept_callback: Optional[Callable] = None,
    on_cancel_callback: Optional[Callable] = None,
    on_chat_callback: Optional[Callable] = None,
    on_support_callback: Optional[Callable] = None,
) -> int:
    """
    Render a container of multiple order boxes with filtering and view options.

    Args:
        orders: List of order dictionaries from Firebase
        user_role: Current user role
        filter_status: Optional status filter (e.g., "Searching for Driver")
        view_mode: "list" for vertical list, "grid" for columnar grid
        max_orders: Maximum orders to display (None = all)
        on_accept_callback: Callback for accepting orders
        on_cancel_callback: Callback for cancelling orders
        on_chat_callback: Callback for opening chat
        on_support_callback: Callback for requesting support

    Returns:
        Number of orders displayed
    """
    try:
        if not orders:
            st.info("📭 No orders available")
            return 0
        
        # Filter orders
        filtered_orders = orders
        if filter_status:
            filtered_orders = [o for o in orders if o.get("status") == filter_status]
        
        if max_orders:
            filtered_orders = filtered_orders[:max_orders]
        
        if not filtered_orders:
            st.warning(f"No orders with status: {filter_status}")
            return 0
        
        # Display count
        st.caption(f"📦 Showing {len(filtered_orders)} order(s)")
        
        # Render based on view mode
        if view_mode == "grid":
            # Grid layout (3 columns)
            cols = st.columns(3)
            for idx, order in enumerate(filtered_orders):
                with cols[idx % 3]:
                    render_order_box(
                        order=order,
                        user_role=user_role,
                        on_accept_callback=on_accept_callback,
                        on_cancel_callback=on_cancel_callback,
                        on_chat_callback=on_chat_callback,
                        on_support_callback=on_support_callback,
                        compact_mode=True
                    )
        else:
            # List layout (full width)
            for order in filtered_orders:
                render_order_box(
                    order=order,
                    user_role=user_role,
                    on_accept_callback=on_accept_callback,
                    on_cancel_callback=on_cancel_callback,
                    on_chat_callback=on_chat_callback,
                    on_support_callback=on_support_callback,
                    compact_mode=False
                )
        
        return len(filtered_orders)
    
    except Exception as e:
        logger.error(f"Error rendering order box container: {str(e)}")
        st.error(f"Error displaying orders: {str(e)}")
        return 0


# ============================================================================
# ORDER BOX DASHBOARD (ADVANCED ANALYTICS)
# ============================================================================

def render_order_statistics_dashboard(orders: List[Dict]) -> None:
    """
    Render order statistics and insights dashboard.

    Args:
        orders: List of order dictionaries
    """
    try:
        if not orders:
            st.info("No orders to analyze")
            return
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(orders)
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Orders", len(df))
        
        with col2:
            total_revenue = df["price"].sum() if "price" in df.columns else 0
            st.metric("Total Revenue", f"EGP {total_revenue:,.2f}")
        
        with col3:
            completed = len(df[df["status"] == "Completed"]) if "status" in df.columns else 0
            st.metric("Completed", completed)
        
        with col4:
            pending = len(df[df["status"] == "Searching for Driver"]) if "status" in df.columns else 0
            st.metric("Pending", pending)
        
        st.divider()
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            if "status" in df.columns and not df.empty:
                status_counts = df["status"].value_counts()
                st.bar_chart(status_counts, use_container_width=True)
        
        with col_chart2:
            if "type" in df.columns and not df.empty:
                type_counts = df["type"].value_counts()
                st.pie_chart(type_counts, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error rendering order statistics: {str(e)}")
        st.warning("Error displaying order statistics")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_status_config(status: str) -> Dict[str, str]:
    """Get color and icon configuration for order status."""
    status_map = {
        "Searching for Driver": {"color": "#FFA500", "icon": "🔍"},
        "Driver En Route": {"color": "#4CAF50", "icon": "🚗"},
        "Completed": {"color": "#2196F3", "icon": "✅"},
        "Cancelled": {"color": "#F44336", "icon": "❌"},
        "Pending Manual Review": {"color": "#FF9800", "icon": "⏳"},
        "Rejected": {"color": "#F44336", "icon": "❌"},
        "Active": {"color": "#4CAF50", "icon": "✅"},
    }
    return status_map.get(status, {"color": "#9E9E9E", "icon": "❓"})


def _render_order_actions(
    order_id: str,
    status: str,
    user_role: str,
    order: Dict,
    on_accept_callback: Optional[Callable],
    on_cancel_callback: Optional[Callable],
    on_chat_callback: Optional[Callable],
    on_support_callback: Optional[Callable],
) -> None:
    """Render action buttons based on user role and order status."""
    try:
        action_cols = st.columns([1, 1, 1, 1])
        
        # DRIVER: Accept Order
        if user_role == "Driver" and status == "Searching for Driver":
            with action_cols[0]:
                if st.button(f"✅ Accept {order_id}", key=f"accept_{order_id}", use_container_width=True):
                    if on_accept_callback:
                        on_accept_callback(order)
                    else:
                        st.error("Accept callback not configured")
        
        # CUSTOMER: Chat
        if user_role in ["Customer", "Driver", "Admin"]:
            with action_cols[1]:
                if st.button(f"💬 Chat {order_id}", key=f"chat_{order_id}", use_container_width=True):
                    if on_chat_callback:
                        on_chat_callback(order_id)
                    else:
                        st.info("Chat feature not available")
        
        # CUSTOMER: Request Support
        if user_role == "Customer" and status != "Cancelled":
            with action_cols[2]:
                if st.button(f"🚨 Support {order_id}", key=f"support_{order_id}", use_container_width=True):
                    if on_support_callback:
                        on_support_callback(order_id)
                    else:
                        st.error("Support callback not configured")
        
        # CUSTOMER: Cancel Order
        if user_role == "Customer" and status not in ["Cancelled", "Completed"]:
            with action_cols[3]:
                if st.button(f"❌ Cancel {order_id}", key=f"cancel_{order_id}", use_container_width=True):
                    if on_cancel_callback:
                        on_cancel_callback(order_id)
                    else:
                        st.error("Cancel callback not configured")
    
    except Exception as e:
        logger.error(f"Error rendering order actions: {str(e)}")


# ============================================================================
# REAL-TIME ORDER UPDATES (AUTO-REFRESH HELPER)
# ============================================================================

def setup_order_box_auto_refresh(refresh_interval: int = 3) -> None:
    """
    Setup auto-refresh for order boxes using Streamlit's session state.
    Call this once at the top of your page.

    Args:
        refresh_interval: Refresh interval in seconds
    """
    if "order_box_last_refresh" not in st.session_state:
        st.session_state["order_box_last_refresh"] = datetime.now()
    
    if (datetime.now() - st.session_state["order_box_last_refresh"]).seconds >= refresh_interval:
        st.session_state["order_box_last_refresh"] = datetime.now()
        st.rerun()
