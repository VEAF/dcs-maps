"""Read/write reference points ``(x, y, lat, lon)``.

``x`` = North, ``y`` = East (see :mod:`dcs_coords.convert`). Three sources:

- ``dcs.log`` produced by ``tools/export_points.lua`` (``DCSXFORM;x;z;lat;lon`` lines);
- CSV ``x,y,lat,lon`` (with header);
- JSON: list of objects ``{"x":..., "y":..., "lat":..., "lon":...}``.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Point:
    """A calibration point. ``x`` = North (DCS x), ``y`` = East (DCS z)."""

    x: float
    y: float
    lat: float
    lon: float


# The Lua script writes: DCSXFORM;<x=North>;<z=East>;<lat>;<lon>
_NUM = r"-?\d+(?:\.\d+)?"
DCSXFORM_RE = re.compile(
    rf"DCSXFORM;(?P<x>{_NUM});(?P<z>{_NUM});(?P<lat>{_NUM});(?P<lon>{_NUM})"
)

# ...and one header line: DCSXFORM;THEATRE;<codified name>  (e.g. PersianGulf, SinaiMap)
THEATRE_RE = re.compile(r"DCSXFORM;THEATRE;(?P<name>[^\s;]+)")


def parse_log(path: str | Path) -> tuple[str | None, list[Point]]:
    """Parse a ``dcs.log`` into ``(theatre, points)`` for the **last** export run.

    A single ``dcs.log`` may accumulate several runs (e.g. when several maps are
    flown one after another in the same session). We therefore keep only the last
    detected ``DCSXFORM;THEATRE;<name>`` line and the points that follow it, so the
    result is always coherent. If no theatre line is present, ``theatre`` is
    ``None`` and every point in the file is returned.
    """
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()

    theatre: str | None = None
    start = 0  # first line index to read points from (after the last theatre line)
    for i, line in enumerate(lines):
        m = THEATRE_RE.search(line)
        if m:
            theatre = m["name"]
            start = i + 1

    points: list[Point] = []
    for line in lines[start:]:
        m = DCSXFORM_RE.search(line)
        if m:
            points.append(
                Point(x=float(m["x"]), y=float(m["z"]), lat=float(m["lat"]), lon=float(m["lon"]))
            )
    return theatre, points


def parse_dcs_log(path: str | Path) -> list[Point]:
    """Points of the last export run in a ``dcs.log`` (see :func:`parse_log`)."""
    _, points = parse_log(path)
    if not points:
        raise ValueError(
            f"No 'DCSXFORM;…' data found in {path}. Did export_points.lua actually run?"
        )
    return points


def parse_theatre_from_log(path: str | Path) -> str | None:
    """Codified theatre of the last export run, or ``None`` (see :func:`parse_log`).

    Matches the ``DCSXFORM;THEATRE;<name>`` line emitted by ``export_points.lua``
    (the value of ``env.mission.theatre``, e.g. ``"Caucasus"``, ``"SinaiMap"``).
    """
    return parse_log(path)[0]


def load_points_csv(path: str | Path) -> list[Point]:
    with open(path, newline="", encoding="utf-8") as f:
        return [
            Point(x=float(r["x"]), y=float(r["y"]), lat=float(r["lat"]), lon=float(r["lon"]))
            for r in csv.DictReader(f)
        ]


def load_points_json(path: str | Path) -> list[Point]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Point(x=float(d["x"]), y=float(d["y"]), lat=float(d["lat"]), lon=float(d["lon"]))
        for d in data
    ]


def load_points(log: str | Path | None = None, points: str | Path | None = None) -> list[Point]:
    """Load points from a ``dcs.log`` (``log=``) or a CSV/JSON file (``points=``)."""
    if log:
        return parse_dcs_log(log)
    if points:
        return load_points_json(points) if str(points).lower().endswith(".json") else load_points_csv(points)
    raise ValueError("Provide log= (dcs.log) or points= (CSV/JSON).")


def save_points_csv(path: str | Path, points: list[Point]) -> None:
    """Save points as CSV (``x,y,lat,lon``) for reproducibility."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "lat", "lon"])
        for p in points:
            w.writerow([f"{p.x:.3f}", f"{p.y:.3f}", f"{p.lat:.9f}", f"{p.lon:.9f}"])


# --------------------------------------------------------------------------- #
# dcs.log discovery
# --------------------------------------------------------------------------- #
_SAVED_GAMES_GLOB = "DCS*/Logs/dcs.log"  # covers DCS, DCS.openbeta, …


def _saved_games_dirs() -> list[Path]:
    base = Path.home() / "Saved Games"
    return [base] if base.exists() else []


def find_dcs_log(bases: list[Path] | None = None) -> Path | None:
    """Best-effort lookup of DCS' ``dcs.log`` under *Saved Games*.

    Searches ``<Saved Games>/DCS*/Logs/dcs.log`` (e.g. ``DCS`` or
    ``DCS.openbeta``) and returns the **most recently modified** match — the one
    most likely written by the latest export run. Returns ``None`` if nothing is
    found. ``bases`` overrides the search roots (used by tests).
    """
    roots = bases if bases is not None else _saved_games_dirs()
    matches: list[Path] = []
    for root in roots:
        matches.extend(Path(root).glob(_SAVED_GAMES_GLOB))
    return max(matches, key=lambda p: p.stat().st_mtime) if matches else None
