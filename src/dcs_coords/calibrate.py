"""Calibration: recover a DCS map's ``lon_0``, ``x_0``, ``y_0``.

The projection model is identical for every DCS map (``tmerc``, ``lat_0=0``,
``k_0=0.9996``, WGS84, ``axis=neu``). Only three parameters vary; we recover
them from a list of ``(x=North, y=East, lat, lon)`` points exported from the game:

1. for each integer ``lon_0`` candidate, project the ``(lat, lon)`` with no
   offset (``x_0=y_0=0``); the residuals ``y - easting`` and ``x - northing``
   must be **constant** for the correct ``lon_0`` (minimal variance);
2. ``x_0`` / ``y_0`` are then the mean of those residuals;
3. reproject with the recovered parameters and report the residual (metres).

No non-linear optimisation: an integer search over ``lon_0`` is enough.
"""

import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import typer
from pyproj import CRS, Transformer
from rich import box
from rich.console import Console
from rich.table import Table

from .ingest import Point, find_dcs_log, load_points, parse_log, save_points_csv
from .maps import MAPS_YAML, PROJ_TEMPLATE, available_maps, set_map

# Residual alert threshold: beyond this the tmerc model is suspect.
RESIDUAL_WARN_M = 1.0


@dataclass
class Calibration:
    map_name: str
    lon_0: int
    x_0: float
    y_0: float
    residual_max_m: float
    residual_rms_m: float
    n_points: int

    def proj_string(self) -> str:
        return PROJ_TEMPLATE.format(lon_0=self.lon_0, x_0=self.x_0, y_0=self.y_0)


def _raw_transformer(lon_0: int) -> Transformer:
    """tmerc WGS84 with no offset (x_0=y_0=0) for the given central meridian."""
    crs = CRS.from_proj4(
        f"+proj=tmerc +lat_0=0 +lon_0={lon_0} +k_0=0.9996 "
        f"+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs +axis=neu"
    )
    return Transformer.from_crs("EPSG:4326", crs, always_xy=True)


def calibrate_from_points(
    map_name: str,
    points: Sequence[Point],
    lon_0_candidates: Iterable[int] | None = None,
) -> Calibration:
    """Calibrate a map from ``(x=North, y=East, lat, lon)`` points."""
    pts = list(points)
    if len(pts) < 3:
        raise ValueError("At least 3 points are required to calibrate.")

    if lon_0_candidates is None:
        lons = [p.lon for p in pts]
        lon_0_candidates = range(math.floor(min(lons)) - 1, math.ceil(max(lons)) + 2)

    best: tuple[float, int, float, float] | None = None
    for lon_0 in lon_0_candidates:
        t = _raw_transformer(lon_0)
        d_east, d_north = [], []
        for p in pts:
            easting, northing = t.transform(p.lon, p.lat)
            d_east.append(p.y - easting)  # y (East)  = easting  + x_0  ->  x_0 = y - easting
            d_north.append(p.x - northing)  # x (North) = northing + y_0  ->  y_0 = x - northing
        score = statistics.pvariance(d_east) + statistics.pvariance(d_north)
        if best is None or score < best[0]:
            best = (score, lon_0, statistics.fmean(d_east), statistics.fmean(d_north))

    assert best is not None
    _, lon_0, x_0, y_0 = best

    # Residual: reproject with the recovered parameters and measure ground error.
    t = _raw_transformer(lon_0)
    max_d, sq_sum = 0.0, 0.0
    for p in pts:
        easting, northing = t.transform(p.lon, p.lat)
        d = math.hypot((easting + x_0) - p.y, (northing + y_0) - p.x)
        max_d = max(max_d, d)
        sq_sum += d * d
    rms = math.sqrt(sq_sum / len(pts))

    return Calibration(map_name, int(lon_0), x_0, y_0, max_d, rms, len(pts))


def _write_map(calib: Calibration) -> None:
    set_map(calib.map_name, calib.lon_0, calib.x_0, calib.y_0)


# --------------------------------------------------------------------------- #
# CLI (Typer + Rich)
# --------------------------------------------------------------------------- #
app = typer.Typer(add_completion=False, no_args_is_help=True, help="DCS coordinate tools.")
_out = Console()
_err = Console(stderr=True)


@app.command("maps")
def cmd_maps() -> None:
    """List known maps."""
    for name in available_maps():
        _out.print(name)


@app.command("generate")
def cmd_generate(
    out: Path = typer.Option(Path("exports"), "--out", help="Output directory for the generated files."),
) -> None:
    """Generate maps.{yaml,json,md,py} with the full projection parameters (for reuse)."""
    from .export import generate

    paths = generate(out)
    for p in paths:
        _out.print(f"[green]ok[/] {p}")
    _out.print(
        f"\n[bold]{len(paths)}[/] files written to [cyan]{out}[/] "
        f"for [bold]{len(available_maps())}[/] maps."
    )


@app.command("calibrate")
def cmd_calibrate(
    map_name: Optional[str] = typer.Option(
        None, "--map", help="Map name (e.g. Sinai). Auto-detected from the log if omitted."
    ),
    log: Optional[Path] = typer.Option(
        None, "--log", exists=True, dir_okay=False,
        help="Path to dcs.log. Auto-discovered under Saved Games if neither --log nor --points is given.",
    ),
    points: Optional[Path] = typer.Option(
        None, "--points", exists=True, dir_okay=False, help="CSV/JSON of points (x,y,lat,lon)."
    ),
    write: bool = typer.Option(False, "--write", help="Write the result into maps.yaml."),
    save_points: Optional[Path] = typer.Option(
        None, "--save-points", help="Copy the points used to this CSV."
    ),
) -> None:
    """Calibrate a map from exported points (a dcs.log or a CSV/JSON)."""
    if log is not None and points is not None:
        _err.print("[bold red]Provide at most one of[/] --log [bold red]or[/] --points.")
        raise typer.Exit(2)
    if log is None and points is None:
        # Neither given: try to find dcs.log under Saved Games.
        log = find_dcs_log()
        if log is None:
            _err.print(
                "[bold red]No dcs.log found.[/] Pass [cyan]--log[/] (or [cyan]--points[/]) "
                r"explicitly — looked under [dim]~\Saved Games\DCS*\Logs[/]."
            )
            raise typer.Exit(2)
        _out.print(f"Using log: [cyan]{log}[/]  [dim](auto-discovered, use --log to override)[/]")

    # Read points; for a log, also auto-detect the theatre of the last run.
    if log:
        detected, pts = parse_log(log)
    else:
        detected, pts = None, load_points(points=points)

    # Resolve the map name: explicit --map, else the theatre from the log.
    resolved = map_name or detected
    if resolved is None:
        _err.print(
            "[bold red]No --map given and no theatre found in the log.[/] "
            "Pass [cyan]--map[/] explicitly."
        )
        raise typer.Exit(2)
    if map_name and detected and detected != map_name:
        _err.print(
            f"[yellow]![/] --map [cyan]{map_name}[/] differs from log theatre "
            f"[cyan]{detected}[/]; using [cyan]{map_name}[/]."
        )

    if len(pts) < 3:
        _err.print(
            f"[bold red]Not enough points[/] ({len(pts)}) to calibrate (need >= 3). "
            "Check the log / export."
        )
        raise typer.Exit(2)

    calib = calibrate_from_points(resolved, pts)

    if not map_name and detected:
        _out.print(f"Detected map: [bold cyan]{detected}[/]  [dim](env.mission.theatre)[/]")

    within = calib.residual_max_m <= RESIDUAL_WARN_M
    res_style = "green" if within else "bold red"
    table = Table(show_header=False, box=box.SIMPLE, pad_edge=False)
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Map", f"[cyan]{calib.map_name}[/]")
    table.add_row("Points", str(calib.n_points))
    table.add_row("lon_0", str(calib.lon_0))
    table.add_row("x_0 (false E)", f"{calib.x_0:.6f}")
    table.add_row("y_0 (false N)", f"{calib.y_0:.6f}")
    table.add_row("Residual max", f"[{res_style}]{calib.residual_max_m * 100:.3f} cm[/]")
    table.add_row("Residual RMS", f"[{res_style}]{calib.residual_rms_m * 100:.3f} cm[/]")
    _out.print(table)
    _out.print(f"[dim]PROJ:[/] {calib.proj_string()}")

    if save_points:
        save_points_csv(save_points, pts)
        _out.print(f"Points -> [green]{save_points}[/]")

    if not within:
        _err.print(
            f"\n[bold red]![/] Max residual ([red]{calib.residual_max_m:.2f} m[/]) > "
            f"{RESIDUAL_WARN_M} m: map may not be tmerc, or points are unreliable. "
            "[bold]Entry NOT written.[/]"
        )
        raise typer.Exit(2)

    if write:
        _write_map(calib)
        _out.print(f"\n[green]Written to[/] {MAPS_YAML}")
    else:
        _out.print("\n[dim](add --write to save into maps.yaml)[/]")


if __name__ == "__main__":  # pragma: no cover
    app()
