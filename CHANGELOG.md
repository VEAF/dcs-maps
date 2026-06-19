# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-19

Initial release.

### Added

- `dcs_coords` Python package to convert **DCS World** map coordinates between
  lat/long (WGS84), DCS planar `x, y`, MGRS, and UTM.
- Transverse Mercator (WGS84, `k₀ = 0.9996`) model with exact per-map constants,
  so conversions use real formulas instead of runtime point lists.
- `dcs-coords` command-line interface: `maps` (list maps), `calibrate`
  (add a new map), and `generate` (rebuild the `exports/`).
- Bundled maps: Caucasus, Falklands, Mariana Islands, Nevada, Normandy,
  Persian Gulf, Syria, The Channel, Iraq, and Kola.
- Generated `exports/` data in JSON, YAML, Python, and Markdown. (from DCS version 2.9.25.21402)
- Documentation under `docs/` (adding a map, exports, how it works, developing).

[Unreleased]: https://github.com/VEAF/dcs-maps-coordinates/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/VEAF/dcs-maps-coordinates/releases/tag/v0.1.0
