"""CLI tests (Typer): `maps` listing and `calibrate` with theatre auto-detection.

Uses Typer's CliRunner. A small but self-consistent log is built from a seeded
map (via the real projection) so calibration converges; `--write` is never
passed, so maps.yaml is left untouched.
"""

from typer.testing import CliRunner

from dcs_coords.calibrate import app
from dcs_coords.convert import xy_to_latlon

runner = CliRunner()


def _make_log(tmp_path, theatre="Caucasus"):
    lines = [f"INFO: DCSXFORM;THEATRE;{theatre}", "INFO: DCSXFORM;BEGIN"]
    for x in range(-200_000, 200_001, 100_000):  # North
        for y in range(-200_000, 200_001, 100_000):  # East
            lat, lon = xy_to_latlon(theatre, x, y)
            lines.append(f"INFO: DCSXFORM;{x:.3f};{y:.3f};{lat:.9f};{lon:.9f}")
    p = tmp_path / "dcs.log"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_cli_maps():
    result = runner.invoke(app, ["maps"])
    assert result.exit_code == 0
    assert "Caucasus" in result.output


def test_cli_calibrate_autodetect(tmp_path):
    result = runner.invoke(app, ["calibrate", "--log", str(_make_log(tmp_path, "Caucasus"))])
    assert result.exit_code == 0, result.output
    out = result.output
    assert "Detected map" in out
    assert "Caucasus" in out
    assert "lon_0" in out
    assert "33" in out


def test_cli_calibrate_explicit_map(tmp_path):
    log = _make_log(tmp_path, "Syria")
    result = runner.invoke(app, ["calibrate", "--map", "Syria", "--log", str(log)])
    assert result.exit_code == 0, result.output
    assert "39" in result.output  # Syria lon_0


def test_cli_calibrate_no_map_no_theatre(tmp_path):
    p = tmp_path / "dcs.log"
    p.write_text("INFO: nothing relevant here\n", encoding="utf-8")
    result = runner.invoke(app, ["calibrate", "--log", str(p)])
    assert result.exit_code == 2


def test_cli_calibrate_autodiscovers_log(tmp_path, monkeypatch):
    import dcs_coords.calibrate as cal

    log = _make_log(tmp_path, "Caucasus")
    monkeypatch.setattr(cal, "find_dcs_log", lambda: log)
    result = runner.invoke(app, ["calibrate"])  # no --log / --points
    assert result.exit_code == 0, result.output
    assert "auto-discovered" in result.output
    assert "Caucasus" in result.output


def test_cli_calibrate_no_source_and_none_found(monkeypatch):
    import dcs_coords.calibrate as cal

    # Force discovery to find nothing so the test is deterministic.
    monkeypatch.setattr(cal, "find_dcs_log", lambda: None)
    result = runner.invoke(app, ["calibrate", "--map", "Caucasus"])
    assert result.exit_code == 2
