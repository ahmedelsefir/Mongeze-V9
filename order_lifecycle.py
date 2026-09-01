"""
order_lifecycle.py - Complete Order Lifecycle Management System

Implements the Mrsool-style order lifecycle with defensive coding:
- Order States: pending → bid_accepted → picked_up → in_transit → delivered
- Defensive Wrappers: All database operations wrapped in try-except
- Firestore Integration: All orders stored with full lifecycle tracking
- Accounting Ledger: Financial events logged for transparency

Author: Mongeze Platform
Last Updated: 2026-09-01
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# 📋 ORDER STATE DEFINITIONS (Mrsool-Compatible)
# ============================================================================

class OrderStatus(Enum):
    """Mrsool-compatible order statuses."""
    PENDING = "pending"  # New order waiting for driver bids
    BID_ACCEPTED = "bid_accepted"  # Customer accepted a driver's bid
    PICKED_UP = "picked_up"  # Driver collected the shipment
    IN_TRANSIT = "in_transit"  # Driver is on the way to destination
    DELIVERED = "delivered"  # Order delivered, payment settled
    CANCELLED = "cancelled"  # Order cancelled before completion


# ============================================================================
# 🎯 DATA MODELS (OOP with @dataclass)
# ============================================================================

@dataclass
class DriverBid:
    """Represents a driver's bid for an order."""
    driver_name: str
    driver_id: str
    bid_amount: float
    estimated_pickup_time_min: int
    estimated_delivery_time_min: int
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    bid_status: str = "active"  # active, accepted, rejected
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bid to Firebase-ready dictionary."""
        return {
            "driver_name": self.driver_name,
            "driver_id": self.driver_id,
            "bid_amount": self.bid_amount,
            "estimated_pickup_time_min": self.estimated_pickup_time_min,
            "estimated_delivery_time_min": self.estimated_delivery_time_min,
            "timestamp": self.timestamp,
            "bid_status": self.bid_status,
        }


@dataclass
class OrderLifecycle:
    """Complete order lifecycle management with defensive operations."""
    order_id: str
    customer_name: str
    order_type: str  # "parcel" or "taxi"
    status: OrderStatus = OrderStatus.PENDING
    
    # Location data
    pickup_location: str = ""
    pickup_lat: float = 0.0
    pickup_lon: float = 0.0
    destination_location: str = ""
    dest_lat: float = 0.0
    dest_lon: float = 0.0
    
    # Pricing
    customer_budget: float = 0.0
    final_price: Optional[float] = None
    payment_method: str = "cash"  # cash, wallet, paymob
    
    # Driver details
    assigned_driver: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    
    # Bidding
    bids: List[Dict[str, Any]] = field(default_factory=list)
    accepted_bid_index: Optional[int] = None
    
    # Timeline
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    bid_accepted_at: Optional[str] = None
    picked_up_at: Optional[str] = None
    in_transit_at: Optional[str] = None
    delivered_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    
    # Lifecycle tracking
    lifecycle_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_bid(self, bid: DriverBid) -> bool:
        """Add a driver bid to the order. Defensive wrapper."""
        try:
            if self.status != OrderStatus.PENDING:
                logger.warning(f"Cannot add bid to order {self.order_id} with status {self.status}")
                return False
            
            self.bids.append(bid.to_dict())
            self._log_event("bid_added", {"driver": bid.driver_name, "amount": bid.bid_amount})
            logger.info(f"Bid added to order {self.order_id} by {bid.driver_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding bid to order {self.order_id}: {str(e)}")
            return False
    
    def accept_bid(self, bid_index: int, driver_name: str) -> bool:
        """Accept a driver bid and transition to BID_ACCEPTED state. Defensive."""
        try:
            if bid_index < 0 or bid_index >= len(self.bids):
                logger.warning(f"Invalid bid index {bid_index} for order {self.order_id}")
                return False
            
            if self.status != OrderStatus.PENDING:
                logger.warning(f"Cannot accept bid for order {self.order_id} with status {self.status}")
                return False
            
            bid = self.bids[bid_index]
            self.accepted_bid_index = bid_index
            self.assigned_driver = driver_name
            self.assigned_driver_id = bid.get("driver_id", "")
            self.final_price = bid.get("bid_amount", self.customer_budget)
            self.status = OrderStatus.BID_ACCEPTED
            self.bid_accepted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self._log_event("bid_accepted", {
                "driver": driver_name,
                "final_price": self.final_price,
                "bid_index": bid_index
            })
            logger.info(f"Bid accepted for order {self.order_id}: driver={driver_name}, price={self.final_price}")
            return True
        except Exception as e:
            logger.error(f"Error accepting bid for order {self.order_id}: {str(e)}")
            return False
    
    def mark_picked_up(self, driver_name: str) -> bool:
        """Mark order as picked up. Transition: BID_ACCEPTED → PICKED_UP. Defensive."""
        try:
            if self.status != OrderStatus.BID_ACCEPTED:
                logger.warning(f"Cannot mark as picked up: order {self.order_id} status is {self.status}")
                return False
            
            if self.assigned_driver != driver_name:
                logger.warning(f"Driver {driver_name} not assigned to order {self.order_id}")
                return False
            
            self.status = OrderStatus.PICKED_UP
            self.picked_up_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_event("picked_up", {"driver": driver_name})
            logger.info(f"Order {self.order_id} marked as picked up by {driver_name}")
            return True
        except Exception as e:
            logger.error(f"Error marking order {self.order_id} as picked up: {str(e)}")
            return False
    
    def mark_in_transit(self, driver_name: str) -> bool:
        """Mark order as in transit. Transition: PICKED_UP → IN_TRANSIT. Defensive."""
        try:
            if self.status != OrderStatus.PICKED_UP:
                logger.warning(f"Cannot mark as in transit: order {self.order_id} status is {self.status}")
                return False
            
            if self.assigned_driver != driver_name:
                logger.warning(f"Driver {driver_name} not assigned to order {self.order_id}")
                return False
            
            self.status = OrderStatus.IN_TRANSIT
            self.in_transit_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_event("in_transit", {"driver": driver_name})
            logger.info(f"Order {self.order_id} marked as in transit by {driver_name}")
            return True
        except Exception as e:
            logger.error(f"Error marking order {self.order_id} as in transit: {str(e)}")
            return False
    
    def mark_delivered(self, driver_name: str) -> bool:
        """Mark order as delivered. Transition: IN_TRANSIT → DELIVERED. Defensive."""
        try:
            if self.status != OrderStatus.IN_TRANSIT:
                logger.warning(f"Cannot mark as delivered: order {self.order_id} status is {self.status}")
                return False
            
            if self.assigned_driver != driver_name:
                logger.warning(f"Driver {driver_name} not assigned to order {self.order_id}")
                return False
            
            self.status = OrderStatus.DELIVERED
            self.delivered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_event("delivered", {"driver": driver_name, "final_price": self.final_price})
            logger.info(f"Order {self.order_id} marked as delivered by {driver_name}")
            return True
        except Exception as e:
            logger.error(f"Error marking order {self.order_id} as delivered: {str(e)}")
            return False
    
    def cancel_order(self, cancelled_by: str, reason: str = "") -> bool:
        """Cancel order at any stage. Defensive."""
        try:
            if self.status == OrderStatus.CANCELLED:
                logger.warning(f"Order {self.order_id} is already cancelled")
                return False
            
            if self.status == OrderStatus.DELIVERED:
                logger.warning(f"Cannot cancel delivered order {self.order_id}")
                return False
            
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._log_event("cancelled", {"cancelled_by": cancelled_by, "reason": reason})
            logger.info(f"Order {self.order_id} cancelled by {cancelled_by}: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {self.order_id}: {str(e)}")
            return False
    
    def _log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log lifecycle event. Defensive."""
        try:
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "details": details,
            }
            self.lifecycle_events.append(event)
        except Exception as e:
            logger.error(f"Error logging event for order {self.order_id}: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complete lifecycle to Firebase-ready dictionary. Defensive."""
        try:
            return {
                "order_id": self.order_id,
                "customer_name": self.customer_name,
                "order_type": self.order_type,
                "status": self.status.value,
                "pickup_location": self.pickup_location,
                "pickup_lat": self.pickup_lat,
                "pickup_lon": self.pickup_lon,
                "destination_location": self.destination_location,
                "dest_lat": self.dest_lat,
                "dest_lon": self.dest_lon,
                "customer_budget": self.customer_budget,
                "final_price": self.final_price,
                "payment_method": self.payment_method,
                "assigned_driver": self.assigned_driver,
                "assigned_driver_id": self.assigned_driver_id,
                "bids": self.bids,
                "accepted_bid_index": self.accepted_bid_index,
                "created_at": self.created_at,
                "bid_accepted_at": self.bid_accepted_at,
                "picked_up_at": self.picked_up_at,
                "in_transit_at": self.in_transit_at,
                "delivered_at": self.delivered_at,
                "cancelled_at": self.cancelled_at,
                "lifecycle_events": self.lifecycle_events,
            }
        except Exception as e:
            logger.error(f"Error converting order {self.order_id} to dict: {str(e)}")
            return {}


# ============================================================================
# 🔧 DEFENSIVE DATABASE OPERATIONS
# ============================================================================

def create_order_lifecycle(
    order_id: str,
    customer_name: str,
    order_type: str,
    pickup_location: str,
    pickup_lat: float,
    pickup_lon: float,
    destination_location: str,
    dest_lat: float,
    dest_lon: float,
    customer_budget: float,
    payment_method: str = "cash",
    send_to_firebase=None,
) -> Tuple[bool, Optional[str]]:
    """
    Create a new order lifecycle in PENDING state.
    Defensive: Wrapped in try-except and validates Firebase availability.
    """
    try:
        if not send_to_firebase:
            logger.error("send_to_firebase function not provided")
            return False, "Database service unavailable"
        
        lifecycle = OrderLifecycle(
            order_id=order_id,
            customer_name=customer_name,
            order_type=order_type,
            pickup_location=pickup_location,
            pickup_lat=pickup_lat,
            pickup_lon=pickup_lon,
            destination_location=destination_location,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            customer_budget=customer_budget,
            payment_method=payment_method,
        )
        
        payload = lifecycle.to_dict()
        if send_to_firebase(f"order_lifecycles/{order_id}", payload):
            logger.info(f"Order lifecycle created: {order_id}")
            return True, None
        else:
            logger.error(f"Failed to create order lifecycle: {order_id}")
            return False, "Failed to save order to database"
    except Exception as e:
        logger.error(f"Error creating order lifecycle: {str(e)}")
        return False, str(e)


def fetch_order_lifecycle(
    order_id: str,
    fetch_firebase_raw=None,
) -> Tuple[bool, Optional[OrderLifecycle], Optional[str]]:
    """
    Fetch order lifecycle from database.
    Defensive: Wrapped in try-except, handles null/invalid data.
    """
    try:
        if not fetch_firebase_raw:
            logger.error("fetch_firebase_raw function not provided")
            return False, None, "Database service unavailable"
        
        raw_data = fetch_firebase_raw(f"order_lifecycles/{order_id}")
        if not raw_data or not isinstance(raw_data, dict):
            logger.warning(f"Order not found: {order_id}")
            return False, None, f"Order {order_id} not found"
        
        # Reconstruct OrderLifecycle from raw data
        lifecycle = OrderLifecycle(
            order_id=raw_data.get("order_id", order_id),
            customer_name=raw_data.get("customer_name", ""),
            order_type=raw_data.get("order_type", ""),
            status=OrderStatus(raw_data.get("status", "pending")),
            pickup_location=raw_data.get("pickup_location", ""),
            pickup_lat=raw_data.get("pickup_lat", 0.0),
            pickup_lon=raw_data.get("pickup_lon", 0.0),
            destination_location=raw_data.get("destination_location", ""),
            dest_lat=raw_data.get("dest_lat", 0.0),
            dest_lon=raw_data.get("dest_lon", 0.0),
            customer_budget=raw_data.get("customer_budget", 0.0),
            final_price=raw_data.get("final_price"),
            payment_method=raw_data.get("payment_method", "cash"),
            assigned_driver=raw_data.get("assigned_driver"),
            assigned_driver_id=raw_data.get("assigned_driver_id"),
            bids=raw_data.get("bids", []),
            accepted_bid_index=raw_data.get("accepted_bid_index"),
            created_at=raw_data.get("created_at", ""),
            bid_accepted_at=raw_data.get("bid_accepted_at"),
            picked_up_at=raw_data.get("picked_up_at"),
            in_transit_at=raw_data.get("in_transit_at"),
            delivered_at=raw_data.get("delivered_at"),
            cancelled_at=raw_data.get("cancelled_at"),
            lifecycle_events=raw_data.get("lifecycle_events", []),
        )
        
        logger.info(f"Order lifecycle fetched: {order_id}, status={lifecycle.status.value}")
        return True, lifecycle, None
    except Exception as e:
        logger.error(f"Error fetching order lifecycle {order_id}: {str(e)}")
        return False, None, str(e)


def update_order_lifecycle(
    lifecycle: OrderLifecycle,
    update_firebase_node=None,
) -> Tuple[bool, Optional[str]]:
    """
    Update order lifecycle in database.
    Defensive: Wrapped in try-except, validates Firebase availability.
    """
    try:
        if not update_firebase_node:
            logger.error("update_firebase_node function not provided")
            return False, "Database service unavailable"
        
        payload = lifecycle.to_dict()
        if update_firebase_node(f"order_lifecycles/{lifecycle.order_id}", payload):
            logger.info(f"Order lifecycle updated: {lifecycle.order_id}")
            return True, None
        else:
            logger.error(f"Failed to update order lifecycle: {lifecycle.order_id}")
            return False, "Failed to update order in database"
    except Exception as e:
        logger.error(f"Error updating order lifecycle: {str(e)}")
        return False, str(e)


def log_accounting_entry(
    order_id: str,
    entry_type: str,
    amount: float,
    driver_name: str,
    details: Dict[str, Any],
    send_to_firebase=None,
) -> bool:
    """
    Log financial event to accounting ledger.
    Defensive: Wrapped in try-except.
    """
    try:
        if not send_to_firebase:
            logger.error("send_to_firebase function not provided")
            return False
        
        ledger_entry = {
            "order_id": order_id,
            "entry_type": entry_type,  # bid_added, bid_accepted, delivered, cancelled, etc.
            "amount": amount,
            "driver_name": driver_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "details": details,
        }
        
        if send_to_firebase(f"accounting_ledger/{order_id}/{datetime.now().strftime('%s')}", ledger_entry):
            logger.info(f"Accounting entry logged: {order_id}, type={entry_type}")
            return True
        else:
            logger.error(f"Failed to log accounting entry for order: {order_id}")
            return False
    except Exception as e:
        logger.error(f"Error logging accounting entry for order {order_id}: {str(e)}")
        return False
