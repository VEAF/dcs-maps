"""Conversion tests for the seeded maps (no game required)."""

import pytest

from dcs_coords import (
    available_maps,
    latlon_to_mgrs,
    latlon_to_utm,
    latlon_to_xy,
    mgrs_to_latlon,
    utm_to_latlon,
    xy_to_latlon,
    xy_to_mgrs,
    xy_to_utm,
)
from dcs_coords.maps import UnknownMapError

KNOWN = [
    "Caucasus",
    "Syria",
    "PersianGulf",
    "Nevada",
    "Normandy",
    "TheChannel",
    "MarianaIslands",
    "Falklands",
]


def test_available_maps():
    maps = available_maps()
    for m in KNOWN:
        assert m in maps


@pytest.mark.parametrize("map_name", KNOWN)
def test_roundtrip_xy(map_name):
    # Origin (x=0, y=0) -> lat/lon -> x,y must come back to (0, 0).
    lat, lon = xy_to_latlon(map_name, 0.0, 0.0)
    pos = latlon_to_xy(map_name, lat, lon)
    assert abs(pos.x) < 1e-3
    assert abs(pos.y) < 1e-3


@pytest.mark.parametrize("map_name", KNOWN)
def test_roundtrip_offcentre(map_name):
    # A point ~100 km north / 50 km east of the origin must round-trip.
    lat, lon = xy_to_latlon(map_name, 100_000.0, 50_000.0)
    pos = latlon_to_xy(map_name, lat, lon)
    assert pos.x == pytest.approx(100_000.0, abs=1e-3)
    assert pos.y == pytest.approx(50_000.0, abs=1e-3)


def test_caucasus_reference():
    # Reference value from JonathanTurnock/dcs-projections.
    pos = latlon_to_xy("Caucasus", 42.5172, 41.8622)
    assert pos.x == pytest.approx(-252691.234, abs=1.0)  # North (DCS x)
    assert pos.y == pytest.approx(628703.254, abs=1.0)  # East  (DCS z)

    lat, lon = xy_to_latlon("Caucasus", pos.x, pos.y)
    assert lat == pytest.approx(42.5172, abs=1e-5)
    assert lon == pytest.approx(41.8622, abs=1e-5)


def test_unknown_map_raises():
    with pytest.raises(UnknownMapError):
        latlon_to_xy("Atlantis", 0.0, 0.0)


def test_mgrs_roundtrip():
    grid = latlon_to_mgrs(42.5172, 41.8622)
    lat, lon = mgrs_to_latlon(grid)
    assert lat == pytest.approx(42.5172, abs=1e-3)
    assert lon == pytest.approx(41.8622, abs=1e-3)


def test_utm_roundtrip():
    u = latlon_to_utm(42.5172, 41.8622)
    lat, lon = utm_to_latlon(u.easting, u.northing, u.zone, u.band)
    assert lat == pytest.approx(42.5172, abs=1e-6)
    assert lon == pytest.approx(41.8622, abs=1e-6)


def test_xy_to_mgrs_and_utm_consistency():
    # xy -> MGRS/UTM must agree with latlon -> MGRS/UTM for the same point.
    lat, lon = 42.5172, 41.8622
    pos = latlon_to_xy("Caucasus", lat, lon)
    assert xy_to_mgrs("Caucasus", pos.x, pos.y) == latlon_to_mgrs(lat, lon)
    assert xy_to_utm("Caucasus", pos.x, pos.y).zone == latlon_to_utm(lat, lon).zone
