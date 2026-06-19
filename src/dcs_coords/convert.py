"""Coordinate conversion functions.

Conventions (IMPORTANT):

- ``x`` = **North** component (same as the ``x`` of the DCS Lua Vec3).
- ``y`` = **East** component (== the ``z`` of the DCS Lua Vec3, **not** its ``y``!).
  In-game a point is ``{x = North, y = Altitude, z = East}``; here we only deal
  with the ground plane, so our ``y`` maps to the game's ``z``.
- ``lat`` / ``lon`` in decimal degrees, WGS84.

``lat/long`` is the hub: ``x,y`` is map-specific (each theatre has its own
``tmerc`` projection) while MGRS and UTM are global. Composed conversions
(``xy_to_mgrs`` ...) simply chain through ``lat/long``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from pyproj import CRS, Transformer

from .maps import proj_string


class Position(NamedTuple):
    """DCS planar coordinates. ``x`` = North (DCS x), ``y`` = East (DCS z)."""

    x: float
    y: float


class UTMPosition(NamedTuple):
    easting: float
    northing: float
    zone: int
    band: str  # latitude band letter (C..X)


# --------------------------------------------------------------------------- #
# lat/long <-> x,y  (per map)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def _transformer(map_name: str) -> Transformer:
    """Memoised EPSG:4326 (lat/long) -> DCS map CRS transformer.

    ``always_xy=True`` normalises I/O to (lon/easting, lat/northing) order,
    regardless of the ``+axis=neu`` present in the PROJ string.
    """
    crs = CRS.from_proj4(proj_string(map_name))
    return Transformer.from_crs("EPSG:4326", crs, always_xy=True)


def latlon_to_xy(map_name: str, lat: float, lon: float) -> Position:
    """``(lat, lon)`` WGS84 -> ``Position(x=North, y=East)`` for the given map."""
    easting, northing = _transformer(map_name).transform(lon, lat)
    return Position(x=northing, y=easting)


def xy_to_latlon(map_name: str, x: float, y: float) -> tuple[float, float]:
    """``Position(x=North, y=East)`` -> ``(lat, lon)`` WGS84 for the given map."""
    lon, lat = _transformer(map_name).transform(y, x, direction="INVERSE")
    return lat, lon


# --------------------------------------------------------------------------- #
# lat/long <-> UTM  (global)
# --------------------------------------------------------------------------- #
def latlon_to_utm(lat: float, lon: float) -> UTMPosition:
    import utm

    easting, northing, zone, band = utm.from_latlon(lat, lon)
    return UTMPosition(easting=easting, northing=northing, zone=zone, band=band)


def utm_to_latlon(easting: float, northing: float, zone: int, band: str) -> tuple[float, float]:
    import utm

    lat, lon = utm.to_latlon(easting, northing, zone, band)
    return lat, lon


# --------------------------------------------------------------------------- #
# lat/long <-> MGRS  (global)
# --------------------------------------------------------------------------- #
def latlon_to_mgrs(lat: float, lon: float, precision: int = 5) -> str:
    """``(lat, lon)`` -> MGRS string. ``precision`` = digits per axis (0..5)."""
    import mgrs

    return mgrs.MGRS().toMGRS(lat, lon, MGRSPrecision=precision)


def mgrs_to_latlon(grid: str) -> tuple[float, float]:
    """MGRS string -> ``(lat, lon)`` (cell centre)."""
    import mgrs

    lat, lon = mgrs.MGRS().toLatLon(grid.strip())
    return lat, lon


# --------------------------------------------------------------------------- #
# x,y <-> MGRS / UTM  (composed, via lat/long)
# --------------------------------------------------------------------------- #
def xy_to_mgrs(map_name: str, x: float, y: float, precision: int = 5) -> str:
    lat, lon = xy_to_latlon(map_name, x, y)
    return latlon_to_mgrs(lat, lon, precision)


def mgrs_to_xy(map_name: str, grid: str) -> Position:
    lat, lon = mgrs_to_latlon(grid)
    return latlon_to_xy(map_name, lat, lon)


def xy_to_utm(map_name: str, x: float, y: float) -> UTMPosition:
    lat, lon = xy_to_latlon(map_name, x, y)
    return latlon_to_utm(lat, lon)


def utm_to_xy(map_name: str, easting: float, northing: float, zone: int, band: str) -> Position:
    lat, lon = utm_to_latlon(easting, northing, zone, band)
    return latlon_to_xy(map_name, lat, lon)
