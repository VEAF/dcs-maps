"""DCS map registry and projection parameters.

Parameters live in ``data/maps.yaml`` (next to this module), validated in editors
by ``data/maps.schema.json`` (wired via the ``# yaml-language-server:`` modeline
at the top of the YAML). Each entry stores only the three values that vary
between maps:

```yaml
Caucasus:
  lon_0: 33          # central meridian (degrees)
  x_0: -99516.99...  # false easting (m)
  y_0: -4998114.9... # false northing (m)
```

The rest of the Transverse Mercator model is identical for every DCS map and is
baked into :data:`PROJ_TEMPLATE`. Keys are the codified ``env.mission.theatre``
names (e.g. ``Caucasus``, ``PersianGulf``, ``SinaiMap``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_DATA_DIR = Path(__file__).resolve().parent / "data"
MAPS_YAML = _DATA_DIR / "maps.yaml"

# Common model for every DCS map; only lon_0/x_0/y_0 are substituted.
PROJ_TEMPLATE = (
    "+proj=tmerc +lat_0=0 +lon_0={lon_0} +k_0=0.9996 "
    "+x_0={x_0} +y_0={y_0} +towgs84=0,0,0,0,0,0,0 "
    "+units=m +vunits=m +ellps=WGS84 +no_defs +axis=neu"
)

# Re-emitted on every write so editor validation keeps working after `calibrate --write`.
_YAML_HEADER = (
    "# yaml-language-server: $schema=maps.schema.json\n"
    "# DCS map projection parameters — managed by `dcs-coords calibrate`.\n"
    "# Only lon_0 (central meridian), x_0 (false easting) and y_0 (false northing)\n"
    "# vary per map; the rest of the tmerc model is fixed in code (k_0=0.9996, WGS84).\n"
    "# Keys are the codified env.mission.theatre names.\n"
)


class UnknownMapError(KeyError):
    """Raised when a requested map is not in the registry."""


def _read() -> dict[str, dict]:
    return yaml.safe_load(MAPS_YAML.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict]:
    return _read()


def reload() -> None:
    """Clear the registry cache (after a write, or when ``MAPS_YAML`` is swapped)."""
    _registry.cache_clear()


def available_maps() -> list[str]:
    """Sorted list of known maps."""
    return sorted(_registry().keys())


def map_params(map_name: str) -> dict:
    """``{lon_0, x_0, y_0}`` for the map, or ``UnknownMapError`` if unknown."""
    try:
        return _registry()[map_name]
    except KeyError:
        raise UnknownMapError(
            f"Unknown map: {map_name!r}. "
            f"Available maps: {', '.join(available_maps())}"
        ) from None


def proj_string(map_name: str) -> str:
    """Full PROJ string for the map, built from its parameters and the template."""
    p = map_params(map_name)
    return PROJ_TEMPLATE.format(lon_0=p["lon_0"], x_0=p["x_0"], y_0=p["y_0"])


def full_params(map_name: str) -> dict:
    """Every projection parameter for the map, self-contained and reusable.

    Expands the fixed tmerc model (constant for all DCS maps) together with the
    map-specific ``lon_0/x_0/y_0`` and the assembled ``proj4`` string. Field
    order matches the PROJ string for readability.
    """
    p = map_params(map_name)
    return {
        "proj": "tmerc",
        "lat_0": 0,
        "lon_0": p["lon_0"],
        "k_0": 0.9996,
        "x_0": p["x_0"],
        "y_0": p["y_0"],
        "towgs84": "0,0,0,0,0,0,0",
        "units": "m",
        "vunits": "m",
        "ellps": "WGS84",
        "no_defs": True,
        "axis": "neu",
        "proj4": proj_string(map_name),
    }


def set_map(map_name: str, lon_0: int, x_0: float, y_0: float) -> None:
    """Add/update a map in ``maps.yaml`` and refresh the cache."""
    data = _read()
    data[map_name] = {"lon_0": int(lon_0), "x_0": float(x_0), "y_0": float(y_0)}
    body = yaml.safe_dump(data, sort_keys=True, default_flow_style=False, allow_unicode=True)
    MAPS_YAML.write_text(_YAML_HEADER + body, encoding="utf-8")
    reload()
