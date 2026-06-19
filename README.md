# DCS Maps

A simple tool to extract some map data to help Mission Makers and developers.

Python package to convert coordinates for **DCS World** maps:

- **lat/long** (decimal degrees, WGS84)
- **x, y** (DCS planar coordinates — **map-specific**)
- **MGRS** and **UTM** (global)

Every DCS map is a Transverse Mercator projection on WGS84 (`k₀ = 0.9996`).
The package ships the exact constants for the maps below, so conversions are a
**real formula** — no point lists carried at runtime. A calibration tool +
in-game Lua script let you add any map you own (see
[Adding a new map](docs/adding-a-map.md)).

Bundled maps: see [exports/maps.md](exports/maps.md)

---

## Coordinate conventions (read this first)

| This package | Meaning            | DCS Lua `Vec3` |
|--------------|--------------------|----------------|
| `x`          | **North**          | `x`            |
| `y`          | **East**           | **`z`**        |
| (altitude)   | not handled here   | `y`            |

⚠️ **Our `y` is the DCS Lua `z` (East), not its `y`.** In-game a point is
`{x = North, y = Altitude, z = East}`; this package only deals with the ground
plane, so it uses `(x = North, y = East)`. Results come back as a named tuple
`Position(x=..., y=...)` to keep this unambiguous.

`lat/long` in decimal degrees, WGS84. Latitudes north positive, longitudes east
positive.

---

## How to work on this project

### Install

Requires Python ≥ 3.10.

```bash
# inside this repo (development / VEAF workflow)
poetry install

# or as a dependency of another project
pip install .
```

Runtime dependencies: [`pyproj`](https://pyproj4.github.io/pyproj/) (the DCS map
projections), [`utm`](https://pypi.org/project/utm/),
[`mgrs`](https://pypi.org/project/mgrs/), `pyyaml` (the map registry), and
[`typer`](https://typer.tiangolo.com/) + [`rich`](https://rich.readthedocs.io/)
(the `dcs-coords` CLI).

### Python API

```python
from dcs_coords import (
    available_maps,
    latlon_to_xy, xy_to_latlon,
    latlon_to_mgrs, mgrs_to_latlon,
    latlon_to_utm,  utm_to_latlon,
    xy_to_mgrs, mgrs_to_xy,
    xy_to_utm,  utm_to_xy,
)

available_maps()
# ['Caucasus', 'Falklands', 'MarianaIslands', 'Nevada',
#  'Normandy', 'PersianGulf', 'Syria', 'TheChannel']

# --- lat/long <-> x,y (per map) ---
pos = latlon_to_xy("Caucasus", 42.5172, 41.8622)
pos                       # Position(x=-252691.23, y=628703.25)   x=North, y=East
pos.x, pos.y              # (-252691.23, 628703.25)

lat, lon = xy_to_latlon("Caucasus", pos.x, pos.y)   # (42.5172, 41.8622)

# --- MGRS / UTM (global) ---
latlon_to_mgrs(42.5172, 41.8622)        # '37TCK...'  (precision=5 by default)
mgrs_to_latlon("37TCK0000000000")       # (lat, lon) of the cell centre

u = latlon_to_utm(42.5172, 41.8622)     # UTMPosition(easting, northing, zone, band)
utm_to_latlon(u.easting, u.northing, u.zone, u.band)

# --- composed (go through lat/long under the hood) ---
xy_to_mgrs("Caucasus", pos.x, pos.y)    # '37TCK...'
mgrs_to_xy("Caucasus", "37TCK0000000000")
xy_to_utm("Caucasus", pos.x, pos.y)
utm_to_xy("Caucasus", u.easting, u.northing, u.zone, u.band)
```

An unknown map raises `dcs_coords.UnknownMapError` listing the available maps.

### Command line

```bash
poetry run dcs-coords maps          # list known maps
poetry run dcs-coords calibrate ... # add a map — see docs/adding-a-map.md
poetry run dcs-coords generate      # (re)write exports/ — see docs/exports.md
```

---

## Documentation

- [Adding a new map](docs/adding-a-map.md) — export points from the game and
  calibrate the projection constants.
- [Reusing the data elsewhere](docs/exports.md) — the generated `exports/` data
  in JSON / YAML / Python / Markdown.
- [How it works](docs/how-it-works.md) — the tmerc model, runtime, and
  calibration internals.
- [How to develop](docs/developing.md) — dev setup, tests, and code layout.
