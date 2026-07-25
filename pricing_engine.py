"""
pricing_engine.py - Dynamic Pricing & GPS Engine for the Monjez platform.

Implements:
  1. Haversine distance between two lat/lon points (great-circle distance).
  2. Surge factor based on supply/demand ratio of active orders to available drivers.
  3. Dynamic fare calculator: Fare = (BaseFare + d*Rate_km + t*Rate_min) * SurgeFactor.

All functions are null-safe, type-checked, and return None / sensible defaults
on invalid input rather than raising.
"""

import logging
from math import asin, cos, radians, sin, sqrt

logger = logging.getLogger(__name__)

# Earth radius in kilometers (mean radius)
EARTH_RADIUS_KM = 6371.0

# Default fare policy (Egyptian market, EGP)
DEFAULT_BASE_FARE = 20.0
DEFAULT_RATE_PER_KM = 5.0
DEFAULT_RATE_PER_MIN = 1.0
DEFAULT_SURGE_FACTOR = 1.0

# Surge thresholds
SURGE_LOW_SUPPLY_RATIO = 1.5   # orders/drivers > this triggers surge
SURGE_HIGH_SURGE_RATIO = 3.0   # orders/drivers above this caps the surge
MAX_SURGE_FACTOR = 2.5
MIN_SURGE_FACTOR = 1.0


def calculate_distance_haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in kilometers.

    Args:
        lat1, lon1: Latitude/Longitude of the origin in decimal degrees.
        lat2, lon2: Latitude/Longitude of the destination in decimal degrees.

    Returns:
        float: Distance in km rounded to 2 decimals, or None on invalid input.
    """
    try:
        coords = [lat1, lon1, lat2, lon2]
        if not all(isinstance(c, (int, float)) for c in coords):
            logger.warning("Haversine: non-numeric coordinates %s", coords)
            return None
        if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
            logger.warning("Haversine: latitude out of range")
            return None
        if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
            logger.warning("Haversine: longitude out of range")
            return None

        lon1_r, lat1_r, lon2_r, lat2_r = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2_r - lon1_r
        dlat = lat2_r - lat1_r
        a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return round(c * EARTH_RADIUS_KM, 2)
    except Exception as e:
        logger.error("Haversine error: %s", e)
        return None


def estimate_travel_time_minutes(distance_km, avg_speed_kmh=28.0):
    """Estimate travel time in minutes from a distance and average urban speed.

    Args:
        distance_km: Distance in kilometers.
        avg_speed_kmh: Average urban driving speed (default ~28 km/h for Cairo traffic).

    Returns:
        int: Estimated minutes, or 0 on invalid input.
    """
    try:
        if distance_km is None or distance_km < 0:
            return 0
        if avg_speed_kmh <= 0:
            return 0
        return int(round((distance_km / avg_speed_kmh) * 60))
    except Exception:
        return 0


def compute_surge_factor(active_orders, available_drivers):
    """Compute a surge multiplier from supply/demand imbalance.

    Surge kicks in when orders/drivers exceeds SURGE_LOW_SUPPLY_RATIO and
    scales linearly up to MAX_SURGE_FACTOR.

    Args:
        active_orders: Count of currently active (unassigned/in-progress) orders.
        available_drivers: Count of currently available (idle, verified) drivers.

    Returns:
        float: Surge factor in [MIN_SURGE_FACTOR, MAX_SURGE_FACTOR].
    """
    try:
        active_orders = int(active_orders or 0)
        available_drivers = int(available_drivers or 0)

        if available_drivers <= 0:
            # No drivers available -> maximum surge (extreme demand)
            return MAX_SURGE_FACTOR

        ratio = active_orders / available_drivers

        if ratio <= SURGE_LOW_SUPPLY_RATIO:
            return MIN_SURGE_FACTOR

        # Linear scale between low and high surge thresholds
        scale_range = SURGE_HIGH_SURGE_RATIO - SURGE_LOW_SUPPLY_RATIO
        if scale_range <= 0:
            return MAX_SURGE_FACTOR

        progress = (ratio - SURGE_LOW_SUPPLY_RATIO) / scale_range
        surge = MIN_SURGE_FACTOR + progress * (MAX_SURGE_FACTOR - MIN_SURGE_FACTOR)

        return round(min(max(surge, MIN_SURGE_FACTOR), MAX_SURGE_FACTOR), 2)
    except Exception as e:
        logger.error("Surge factor error: %s", e)
        return DEFAULT_SURGE_FACTOR


def calculate_dynamic_fare(distance_km, time_minutes,
                            base_fare=DEFAULT_BASE_FARE,
                            rate_per_km=DEFAULT_RATE_PER_KM,
                            rate_per_min=DEFAULT_RATE_PER_MIN,
                            surge_factor=DEFAULT_SURGE_FACTOR):
    """Dynamic fare calculator.

    Fare = (BaseFare + d * Rate_km + t * Rate_min) * SurgeFactor

    Args:
        distance_km: Trip distance in kilometers.
        time_minutes: Estimated trip duration in minutes.
        base_fare: Fixed base fare (EGP).
        rate_per_km: Per-kilometer rate (EGP).
        rate_per_min: Per-minute rate (EGP).
        surge_factor: Multiplier from compute_surge_factor().

    Returns:
        dict with fare breakdown: base, distance_cost, time_cost,
        subtotal, surge_factor, total. Returns None on invalid input.
    """
    try:
        if distance_km is None or distance_km < 0:
            logger.warning("Dynamic fare: invalid distance %s", distance_km)
            return None
        if time_minutes is None or time_minutes < 0:
            time_minutes = 0
        if surge_factor is None or surge_factor < MIN_SURGE_FACTOR:
            surge_factor = MIN_SURGE_FACTOR

        base = float(base_fare)
        distance_cost = round(float(distance_km) * float(rate_per_km), 2)
        time_cost = round(float(time_minutes) * float(rate_per_min), 2)
        subtotal = round(base + distance_cost + time_cost, 2)
        total = round(subtotal * float(surge_factor), 2)

        return {
            "base_fare": base,
            "distance_km": float(distance_km),
            "distance_cost": distance_cost,
            "time_minutes": int(time_minutes),
            "time_cost": time_cost,
            "subtotal": subtotal,
            "surge_factor": float(surge_factor),
            "total_fare": total,
        }
    except Exception as e:
        logger.error("Dynamic fare error: %s", e)
        return None


def estimate_trip(origin_lat, origin_lon, dest_lat, dest_lon,
                  active_orders=0, available_drivers=0,
                  base_fare=DEFAULT_BASE_FARE,
                  rate_per_km=DEFAULT_RATE_PER_KM,
                  rate_per_min=DEFAULT_RATE_PER_MIN,
                  avg_speed_kmh=28.0):
    """One-shot helper: distance + time + surge + fare for a trip.

    Args:
        origin_lat, origin_lon: Pickup coordinates.
        dest_lat, dest_lon: Destination coordinates.
        active_orders: Active order count for surge.
        available_drivers: Available driver count for surge.
        base_fare, rate_per_km, rate_per_min: Fare policy.
        avg_speed_kmh: Average speed for time estimate.

    Returns:
        dict with distance_km, time_minutes, surge_factor, fare_breakdown,
        or None if coordinates are invalid.
    """
    try:
        distance = calculate_distance_haversine(
            origin_lat, origin_lon, dest_lat, dest_lon
        )
        if distance is None:
            return None

        time_min = estimate_travel_time_minutes(distance, avg_speed_kmh)
        surge = compute_surge_factor(active_orders, available_drivers)
        fare = calculate_dynamic_fare(
            distance, time_min,
            base_fare=base_fare,
            rate_per_km=rate_per_km,
            rate_per_min=rate_per_min,
            surge_factor=surge,
        )
        if fare is None:
            return None

        return {
            "distance_km": distance,
            "time_minutes": time_min,
            "surge_factor": surge,
            "fare": fare,
        }
    except Exception as e:
        logger.error("Estimate trip error: %s", e)
        return None
