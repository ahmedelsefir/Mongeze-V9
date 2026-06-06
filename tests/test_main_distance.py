"""
Tests for the distance calculation and formatting functions in main.py.

These are pure functions with no external dependencies, making them
the highest-value targets for unit testing.
"""

import math
import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers to import only the functions we need from main.py without
# triggering Streamlit page config or Firebase initialization.
# ---------------------------------------------------------------------------

def _import_main_functions():
    """
    Parse main.py and extract standalone functions into a namespace dict.
    We exec the function definitions in an isolated namespace to avoid
    side effects from module-level Streamlit/Firebase calls.
    """
    import ast, textwrap

    with open("main.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    target_funcs = {
        "calculate_distance_haversine",
        "get_live_distance_for_order",
        "format_distance_display",
    }

    func_sources = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            func_sources.append(ast.get_source_segment(source, node))

    # Build a mini-module with the required imports and extracted functions
    import_block = textwrap.dedent("""\
        import logging
        from math import radians, cos, sin, asin, sqrt
        logger = logging.getLogger("test_main")
    """)
    combined = import_block + "\n\n" + "\n\n".join(func_sources)

    ns = {}
    exec(compile(combined, "<test_main_distance>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def funcs():
    return _import_main_functions()


# ===================================================================
# calculate_distance_haversine
# ===================================================================

class TestCalculateDistanceHaversine:
    """Tests for the Haversine distance calculator."""

    def test_same_point_returns_zero(self, funcs):
        result = funcs["calculate_distance_haversine"](30.0, 31.0, 30.0, 31.0)
        assert result == 0.0

    def test_known_distance_cairo_to_alexandria(self, funcs):
        # Cairo (30.0444, 31.2357) -> Alexandria (31.2001, 29.9187)
        dist = funcs["calculate_distance_haversine"](30.0444, 31.2357, 31.2001, 29.9187)
        # Real distance ~180 km; Haversine should be in that ballpark
        assert 170 < dist < 190

    def test_equator_crossing(self, funcs):
        # Points on equator, 1 degree apart in longitude ≈ 111 km
        dist = funcs["calculate_distance_haversine"](0.0, 0.0, 0.0, 1.0)
        assert 110 < dist < 112

    def test_poles_to_equator(self, funcs):
        # North pole (90, 0) to equator (0, 0) = ~10,008 km (quarter of circumference)
        dist = funcs["calculate_distance_haversine"](90.0, 0.0, 0.0, 0.0)
        assert 10000 < dist < 10020

    def test_invalid_non_numeric_returns_none(self, funcs):
        assert funcs["calculate_distance_haversine"]("a", 31.0, 30.0, 31.0) is None

    def test_invalid_lat_out_of_range_returns_none(self, funcs):
        assert funcs["calculate_distance_haversine"](100.0, 31.0, 30.0, 31.0) is None

    def test_invalid_lon_out_of_range_returns_none(self, funcs):
        assert funcs["calculate_distance_haversine"](30.0, 200.0, 30.0, 31.0) is None

    def test_boundary_values_accepted(self, funcs):
        # Extreme valid coordinates
        result = funcs["calculate_distance_haversine"](90.0, 180.0, -90.0, -180.0)
        assert result is not None
        # Pole to pole ≈ 20,015 km
        assert 20000 < result < 20020

    def test_negative_coordinates(self, funcs):
        # Southern hemisphere
        dist = funcs["calculate_distance_haversine"](-33.8688, 151.2093, -37.8136, 144.9631)
        # Sydney to Melbourne ≈ 714 km
        assert 700 < dist < 730

    def test_result_is_rounded_to_two_decimals(self, funcs):
        dist = funcs["calculate_distance_haversine"](30.0444, 31.2357, 31.2001, 29.9187)
        assert dist == round(dist, 2)

    def test_none_coordinate_returns_none(self, funcs):
        assert funcs["calculate_distance_haversine"](None, 31.0, 30.0, 31.0) is None

    def test_integer_coordinates_accepted(self, funcs):
        result = funcs["calculate_distance_haversine"](30, 31, 31, 32)
        assert result is not None and result > 0


# ===================================================================
# get_live_distance_for_order
# ===================================================================

class TestGetLiveDistanceForOrder:
    """Tests for extracting coordinates from an order dict and computing distance."""

    def test_valid_order_returns_distance(self, funcs):
        order = {
            "order_id": "TAXI-001",
            "customer_lat": 30.0444,
            "customer_lon": 31.2357,
            "driver_lat": 30.0500,
            "driver_lon": 31.2400,
        }
        result = funcs["get_live_distance_for_order"](order)
        assert result is not None
        assert result >= 0

    def test_missing_customer_lat_returns_none(self, funcs):
        order = {
            "customer_lon": 31.2357,
            "driver_lat": 30.05,
            "driver_lon": 31.24,
        }
        assert funcs["get_live_distance_for_order"](order) is None

    def test_missing_driver_lon_returns_none(self, funcs):
        order = {
            "customer_lat": 30.0444,
            "customer_lon": 31.2357,
            "driver_lat": 30.05,
        }
        assert funcs["get_live_distance_for_order"](order) is None

    def test_all_coords_none_returns_none(self, funcs):
        order = {
            "customer_lat": None,
            "customer_lon": None,
            "driver_lat": None,
            "driver_lon": None,
        }
        assert funcs["get_live_distance_for_order"](order) is None

    def test_empty_order_returns_none(self, funcs):
        assert funcs["get_live_distance_for_order"]({}) is None

    def test_same_location_returns_zero(self, funcs):
        order = {
            "customer_lat": 30.0,
            "customer_lon": 31.0,
            "driver_lat": 30.0,
            "driver_lon": 31.0,
        }
        assert funcs["get_live_distance_for_order"](order) == 0.0


# ===================================================================
# format_distance_display
# ===================================================================

class TestFormatDistanceDisplay:
    """Tests for the distance display formatter."""

    def test_none_returns_unavailable(self, funcs):
        assert funcs["format_distance_display"](None) == "غير متاح 📍"

    def test_less_than_one_km_shows_meters(self, funcs):
        result = funcs["format_distance_display"](0.5)
        assert "500" in result
        assert "متر" in result

    def test_between_1_and_50_km(self, funcs):
        result = funcs["format_distance_display"](25.0)
        assert "25.0" in result
        assert "كم" in result
        assert "🚕" in result

    def test_above_50_km(self, funcs):
        result = funcs["format_distance_display"](100.0)
        assert "100.0" in result
        assert "🛣️" in result

    def test_exactly_1_km(self, funcs):
        result = funcs["format_distance_display"](1.0)
        assert "كم" in result
        assert "🚕" in result

    def test_exactly_50_km(self, funcs):
        # 50.0 is not < 50, so it falls into the else branch (>= 50)
        result = funcs["format_distance_display"](50.0)
        assert "كم" in result
        assert "🛣️" in result

    def test_zero_distance_shows_meters(self, funcs):
        result = funcs["format_distance_display"](0.0)
        assert "0" in result
        assert "متر" in result

    def test_small_fraction_shows_meters(self, funcs):
        result = funcs["format_distance_display"](0.123)
        assert "123" in result
        assert "متر" in result
