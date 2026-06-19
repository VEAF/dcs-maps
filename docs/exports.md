# Reusing the data elsewhere

[← README](../README.md)

`poetry run dcs-coords generate` expands `maps.yaml` to the **full** projection
parameters (the fixed tmerc model + `lon_0/x_0/y_0` + the assembled `proj4`
string) and writes the same data in four formats under [`exports/`](../exports/),
so it can be reused with or without this package:

| File | For |
|------|-----|
| [`exports/maps.json`](../exports/maps.json) | any language, GIS tools, proj4 strings |
| [`exports/maps.yaml`](../exports/maps.yaml) | config files, human-friendly |
| [`exports/maps.py`](../exports/maps.py)     | typed `Map` dataclass + `MAPS: list[Map]` (+ `MAPS_BY_NAME`), no dependency |
| [`exports/maps.md`](../exports/maps.md)     | quick reference table + PROJ strings |

These files are generated — edit
[`src/dcs_coords/data/maps.yaml`](../src/dcs_coords/data/maps.yaml) (the source)
and re-run `generate`.
