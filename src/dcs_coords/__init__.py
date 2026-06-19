"""dcs_coords — coordinate conversions for DCS World maps.

Function API. ``x`` = North (DCS x), ``y`` = East (DCS z). See
:mod:`dcs_coords.convert` for the conventions.
"""

from __future__ import annotations

from .convert import (
    Position,
    UTMPosition,
    latlon_to_mgrs,
    latlon_to_utm,
    latlon_to_xy,
    mgrs_to_latlon,
    mgrs_to_xy,
    utm_to_latlon,
    utm_to_xy,
    xy_to_latlon,
    xy_to_mgrs,
    xy_to_utm,
)
from .maps import UnknownMapError, available_maps, full_params, proj_string

__version__ = "0.1.0"

__all__ = [
    "available_maps",
    "proj_string",
    "full_params",
    "UnknownMapError",
    "Position",
    "UTMPosition",
    "latlon_to_xy",
    "xy_to_latlon",
    "latlon_to_mgrs",
    "mgrs_to_latlon",
    "latlon_to_utm",
    "utm_to_latlon",
    "xy_to_mgrs",
    "mgrs_to_xy",
    "xy_to_utm",
    "utm_to_xy",
]
