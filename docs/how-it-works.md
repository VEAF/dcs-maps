# How it works

[← README](../README.md)

Every DCS theatre uses the same model; only three parameters change, stored per
map in [`maps.yaml`](../src/dcs_coords/data/maps.yaml) (`lon_0`, `x_0`, `y_0`)
and validated in editors by `maps.schema.json`:

```
+proj=tmerc +lat_0=0 +lon_0=<central meridian> +k_0=0.9996
+x_0=<false easting> +y_0=<false northing>
+ellps=WGS84 +axis=neu +units=m
```

- **Runtime** ([`convert.py`](../src/dcs_coords/convert.py)): a cached
  `pyproj.Transformer` per map. `axis=neu` + `always_xy=True` gives
  `(easting, northing)`, mapped to `(x = North = northing, y = East = easting)`.
- **Calibration** ([`calibrate.py`](../src/dcs_coords/calibrate.py)): for each
  integer `lon_0` candidate, project the sample lat/longs with no offset; the
  correct `lon_0` makes `y − easting` and `x − northing` **constant** (minimal
  variance). `x_0` / `y_0` are then those constants (the means), and the fit is
  validated by reprojection residual. No non-linear solver — an integer search
  on `lon_0` is enough.

The bundled constants come from / are cross-checked against
[JonathanTurnock/dcs-projections](https://github.com/JonathanTurnock/dcs-projections).
