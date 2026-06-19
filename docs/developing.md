# How to develop

[← README](../README.md)

```bash
poetry install            # create the venv + editable install
poetry run pytest -q      # run the test suite
```

The tests need **no game**: `test_known_maps.py` checks round-trips and an
external Caucasus reference value; `test_calibration.py` synthesises points from
the seeded projections and verifies the calibrator recovers the published
constants to sub-centimetre.

## Layout

```
src/dcs_coords/
  __init__.py        public API (re-exports)
  convert.py         lat/long <-> x,y  + MGRS + UTM
  maps.py            registry loader + full_params()
  calibrate.py       calibrate_from_points() + the `dcs-coords` CLI
  ingest.py          parse_log() (theatre + points) + CSV/JSON loaders
  export.py          builds maps.{yaml,json,md,py} from the source
  data/
    maps.yaml         projection params (source of truth: lon_0/x_0/y_0 per map)
    maps.schema.json  JSON Schema for maps.yaml (IDE validation)
tools/
  export_points.lua   in-game grid exporter (-> dcs.log)
exports/             generated full-parameter data (maps.yaml/json/md/py)
points/              raw exported points per map, CSV (reproducibility; --save-points)
tests/
```

`maps.yaml` is validated in-editor by `maps.schema.json` via the
`# yaml-language-server: $schema=maps.schema.json` modeline at the top of the
file (VS Code: install the *YAML* extension by Red Hat). Editing a value that
breaks the schema is flagged inline.

To add a conversion, add the function in `convert.py` and re-export it in
`__init__.py`. To add a map, prefer the calibration flow
([Adding a new map](adding-a-map.md)) over editing `maps.yaml` by hand.
