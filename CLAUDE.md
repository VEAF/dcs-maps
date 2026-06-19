# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`dcs-maps-coordinates` converts coordinates for **DCS World** maps between
lat/long (WGS84), DCS planar `x, y` (map-specific), MGRS, and UTM. Every DCS
theatre is a Transverse Mercator projection on WGS84 (`k₀ = 0.9996`); only three
parameters vary per map (`lon_0`, `x_0`, `y_0`). Conversions are real
projection math (via `pyproj`), not lookup tables.

## Commands

```bash
poetry install                 # venv + editable install
poetry run pytest -q           # full test suite (needs no game installed)
poetry run pytest tests/test_known_maps.py::<name>   # a single test

poetry run dcs-coords maps     # list known maps
poetry run dcs-coords calibrate [--write]            # add/update a map from a dcs.log
poetry run dcs-coords generate # rebuild exports/ after changing maps.yaml
```

Requires Python ≥ 3.10.

## Coordinate convention (critical)

`x` = **North** (DCS Lua `Vec3.x`), `y` = **East** (DCS Lua `Vec3.z`, **not**
its `y`). This package ignores altitude. Results are `Position(x, y)` named
tuples to keep this unambiguous. lat/long is decimal degrees WGS84 (N/E
positive). See the docstring in [src/dcs_coords/convert.py](src/dcs_coords/convert.py).

## Architecture

`lat/long` is the hub: `x,y` is per-map, while MGRS/UTM are global. Composed
conversions (`xy_to_mgrs`, etc.) chain through lat/long — they are thin
compositions, not separate math.

- [src/dcs_coords/maps.py](src/dcs_coords/maps.py) — registry. Loads
  `data/maps.yaml` (cached via `lru_cache`; call `reload()` after writes). The
  full PROJ string is built from `PROJ_TEMPLATE` + the three per-map values.
  `maps.yaml` stores **only** `lon_0/x_0/y_0`; everything else is fixed in code.
- [src/dcs_coords/convert.py](src/dcs_coords/convert.py) — the conversions. One
  cached `pyproj.Transformer` per map (`always_xy=True` normalizes I/O order
  despite the `+axis=neu` in the PROJ string).
- [src/dcs_coords/calibrate.py](src/dcs_coords/calibrate.py) —
  `calibrate_from_points()` + the `dcs-coords` Typer CLI. Calibration does an
  **integer search over `lon_0`**: the correct meridian makes `y − easting` and
  `x − northing` constant (min variance); `x_0/y_0` are those means. No
  non-linear solver. Rejects fits with residual > 1 m.
- [src/dcs_coords/ingest.py](src/dcs_coords/ingest.py) — `parse_log()` reads the
  `dcs.log` produced by the in-game script (theatre auto-detected from
  `env.mission.theatre`; only the **last** theatre block is used) plus CSV/JSON
  loaders.
- [src/dcs_coords/export.py](src/dcs_coords/export.py) — regenerates
  `exports/maps.{yaml,json,md,py}` from the registry (`dcs-coords generate`).
- [tools/export_points.lua](tools/export_points.lua) — in-game grid exporter
  (DO SCRIPT trigger → logs `DCSXFORM` lines via `env.info`, no game-file edits).
- [src/dcs_coords/__init__.py](src/dcs_coords/__init__.py) — public API surface
  (`__all__`). Adding a conversion means adding it in `convert.py` and
  re-exporting here.

## Source of truth & data flow

`data/maps.yaml` is the source of truth for projection params (validated
in-editor by `data/maps.schema.json` via the `# yaml-language-server:` modeline
— `set_map()` re-emits that header on every write so validation survives).
`exports/` is **generated** output — never hand-edit it; run `dcs-coords
generate`. To add a map, prefer the calibration flow
([docs/adding-a-map.md](docs/adding-a-map.md)) over editing `maps.yaml` by hand,
and commit both the YAML change and any saved points.

## Map names

Keys are the codified `env.mission.theatre` values (camelCase, no spaces):
`Caucasus`, `PersianGulf`, `MarianaIslands`, `SinaiMap`, `Kola`, etc. This same
string is the `map_name` argument throughout the API.

## Further docs

[docs/how-it-works.md](docs/how-it-works.md) (model + calibration internals),
[docs/adding-a-map.md](docs/adding-a-map.md), [docs/exports.md](docs/exports.md),
[docs/developing.md](docs/developing.md).
