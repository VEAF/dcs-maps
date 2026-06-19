"""Tests for log/point ingestion, including theatre auto-detection."""

import os

import pytest

from dcs_coords.ingest import find_dcs_log, parse_dcs_log, parse_log, parse_theatre_from_log

_PREFIX = "2026-06-19 10:00:00.001 INFO    SCRIPTING (Main): "

SAMPLE_LOG = (
    f"{_PREFIX}DCSXFORM;THEATRE;PersianGulf\n"
    f"{_PREFIX}DCSXFORM;BEGIN\n"
    f"{_PREFIX}DCSXFORM;100.000;200.000;26.123456789;55.987654321\n"
    f"{_PREFIX}DCSXFORM;-100.500;-200.250;25.000000000;54.500000000\n"
    f"{_PREFIX}DCSXFORM;END;2\n"
)


def _write(tmp_path, text):
    p = tmp_path / "dcs.log"
    p.write_text(text, encoding="utf-8")
    return p


def test_parse_points(tmp_path):
    pts = parse_dcs_log(_write(tmp_path, SAMPLE_LOG))
    assert len(pts) == 2
    assert pts[0].x == 100.0 and pts[0].y == 200.0  # x=North, y=East
    assert pts[0].lat == pytest.approx(26.123456789)
    assert pts[0].lon == pytest.approx(55.987654321)


def test_parse_theatre(tmp_path):
    assert parse_theatre_from_log(_write(tmp_path, SAMPLE_LOG)) == "PersianGulf"


def test_parse_theatre_absent(tmp_path):
    no_theatre = "\n".join(l for l in SAMPLE_LOG.splitlines() if "THEATRE" not in l)
    assert parse_theatre_from_log(_write(tmp_path, no_theatre)) is None


def test_empty_log_raises(tmp_path):
    with pytest.raises(ValueError):
        parse_dcs_log(_write(tmp_path, "nothing useful here\n"))


# Two export runs appended to the same log (e.g. two maps flown in a row).
MULTI_LOG = (
    f"{_PREFIX}DCSXFORM;THEATRE;Caucasus\n"
    f"{_PREFIX}DCSXFORM;BEGIN\n"
    f"{_PREFIX}DCSXFORM;1.000;2.000;40.000000000;30.000000000\n"  # Caucasus run -> ignored
    f"{_PREFIX}DCSXFORM;END;1\n"
    f"{_PREFIX}DCSXFORM;THEATRE;PersianGulf\n"
    f"{_PREFIX}DCSXFORM;BEGIN\n"
    f"{_PREFIX}DCSXFORM;100.000;200.000;26.000000000;55.000000000\n"  # last run -> kept
    f"{_PREFIX}DCSXFORM;300.000;400.000;27.000000000;56.000000000\n"
    f"{_PREFIX}DCSXFORM;END;2\n"
)


def test_multi_theatre_takes_last_run(tmp_path):
    theatre, pts = parse_log(_write(tmp_path, MULTI_LOG))
    assert theatre == "PersianGulf"
    assert len(pts) == 2  # only the points after the last THEATRE line
    assert (pts[0].x, pts[0].y) == (100.0, 200.0)
    assert (pts[1].x, pts[1].y) == (300.0, 400.0)


def test_parse_log_no_theatre_returns_all(tmp_path):
    no_theatre = "\n".join(l for l in MULTI_LOG.splitlines() if "THEATRE" not in l)
    theatre, pts = parse_log(_write(tmp_path, no_theatre))
    assert theatre is None
    assert len(pts) == 3  # all data points, no theatre delimiter


def test_find_dcs_log_picks_most_recent(tmp_path):
    # Two fake installs under one Saved Games root.
    (tmp_path / "DCS" / "Logs").mkdir(parents=True)
    (tmp_path / "DCS.openbeta" / "Logs").mkdir(parents=True)
    older = tmp_path / "DCS" / "Logs" / "dcs.log"
    newer = tmp_path / "DCS.openbeta" / "Logs" / "dcs.log"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    os.utime(older, (1_000_000, 1_000_000))
    os.utime(newer, (2_000_000, 2_000_000))
    assert find_dcs_log(bases=[tmp_path]) == newer


def test_find_dcs_log_none_when_absent(tmp_path):
    assert find_dcs_log(bases=[tmp_path]) is None
