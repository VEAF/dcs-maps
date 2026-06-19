# Adding a new map

[← README](../README.md)

You only need the **game installed for that map**. The procedure exports a grid
of reference points from inside DCS, then derives the three projection
constants. It is fully reproducible and needs **no modification of game files**
(it logs via `env.info`, which is always allowed).

1. **Export points from the game.** In the Mission Editor on the target map,
   create a minimal mission (any date/weather/aircraft). Add a trigger:
   - **Type:** `ONCE`
   - **Condition:** *(none)*
   - **Action:** `DO SCRIPT` → paste the whole of
     [`tools/export_points.lua`](../tools/export_points.lua).

   Run the mission for ~5 seconds, then quit.

2. **Grab the log:** `Saved Games\DCS\Logs\dcs.log`. It now contains lines like
   `... DCSXFORM;<x>;<z>;<lat>;<lon>`.

3. **Calibrate.** The map name is **auto-detected** from the log (the script
   logs `env.mission.theatre`), so `--map` is optional:

   Short version, dry run:
   ```bash
   poetry run dcs-coords calibrate
   ```   

   Short version, write:
   ```bash
   poetry run dcs-coords calibrate --write
   ```   

   Full version (use --help for more information)
   ```bash
   poetry run dcs-coords calibrate \
       --log "C:\Users\<you>\Saved Games\DCS\Logs\dcs.log" \
       --save-points var/SinaiMap.csv \
       --write
   ```

   Output example:

   ```
   Detected map  : SinaiMap  (env.mission.theatre)
   Map           : SinaiMap
   Points        : 121
   lon_0         : 34
   x_0 (false E) : ...
   y_0 (false N) : ...
   Residual max  : 0.01 cm
   PROJ          : +proj=tmerc +lat_0=0 +lon_0=34 +k_0=0.9996 +x_0=... +y_0=... ...
   ```

   Pass `--map <Name>` to override the detected name (and it is **required** when
   calibrating from a CSV/JSON, which carries no theatre line).

   `--log` is **optional** too: when neither `--log` nor `--points` is given, the
   most recent `dcs.log` under `~\Saved Games\DCS*\Logs` is auto-discovered.

4. **Check the residual.** It should be sub-centimetre (a clean `tmerc` fit).
   If `Residual max > 1 m`, the entry is **not** written and a warning is shown
   — the map may not be a plain transverse Mercator, or the export is faulty.

5. `--write` adds the map to
   [`src/dcs_coords/data/maps.yaml`](../src/dcs_coords/data/maps.yaml) (only
   `lon_0`, `x_0`, `y_0`); `--save-points` keeps the raw points for
   reproducibility. **Commit both files.** The map is now usable through the API
   immediately.

You can also calibrate from a CSV/JSON file instead of a log
(`--points file.csv`, columns `x,y,lat,lon`).

> Already have the points from someone else (a map you don't own)? Drop them in
> a CSV and run `calibrate --points ... --map <Name>` — the game is only needed
> to *produce* the points.

**Map names** are the codified `env.mission.theatre` values (camelCase, no
spaces): `Caucasus`, `Nevada`, `PersianGulf`, `Normandy`, `TheChannel`, `Syria`,
`MarianaIslands`, `Falklands`, `SinaiMap`, `Kola`, `Afghanistan`, `GermanyCW`, …
This is the key used in `maps.yaml` and the `map_name` argument throughout the API.

> `dcs.log` accumulates across runs, so you can export several maps in a row in
> one session — the calibrator only uses the **last** theatre block (the last
> `THEATRE` line and the points after it).

After adding a map, refresh the shareable exports: `poetry run dcs-coords generate`
(see [Reusing the data elsewhere](exports.md)).
