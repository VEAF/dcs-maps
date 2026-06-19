"""Tests for the YAML registry: params loading, PROJ building, and writes."""

import pytest

import dcs_coords.maps as m


def test_map_params_caucasus():
    # Tolerant on purpose: x_0/y_0 are ~integers and may be re-calibrated from the
    # game (sub-micron differences), so we don't pin the exact seeded float.
    p = m.map_params("Caucasus")
    assert p["lon_0"] == 33
    assert p["x_0"] == pytest.approx(-99517.0, abs=0.5)
    assert p["y_0"] == pytest.approx(-4998115.0, abs=0.5)


def test_proj_string_built_from_params():
    s = m.proj_string("Caucasus")
    assert "+proj=tmerc" in s
    assert "+lon_0=33" in s
    assert "+k_0=0.9996" in s
    assert "+axis=neu" in s


def test_set_map_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "maps.yaml"
    f.write_text(
        "# yaml-language-server: $schema=maps.schema.json\n"
        "Caucasus:\n  lon_0: 33\n  x_0: -99517.0\n  y_0: -4998115.0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(m, "MAPS_YAML", f)
    m.reload()

    m.set_map("TestLand", 10, 123.5, -456.5)
    m.reload()

    assert "TestLand" in m.available_maps()
    assert m.map_params("TestLand") == {"lon_0": 10, "x_0": 123.5, "y_0": -456.5}

    text = f.read_text(encoding="utf-8")
    assert "# yaml-language-server: $schema=maps.schema.json" in text  # modeline kept
    assert "TestLand" in text and "Caucasus" in text  # existing entry preserved
