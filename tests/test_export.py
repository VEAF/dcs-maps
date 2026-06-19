"""Tests for the multi-format export generator."""

import json

import yaml

from dcs_coords import available_maps
from dcs_coords.export import (
    build_registry,
    generate,
    to_json,
    to_markdown,
    to_python,
    to_yaml,
)

_FULL_KEYS = {
    "proj", "lat_0", "lon_0", "k_0", "x_0", "y_0",
    "towgs84", "units", "vunits", "ellps", "no_defs", "axis", "proj4",
}


def test_build_registry_full_params():
    reg = build_registry()
    assert set(reg) == set(available_maps())
    cauc = reg["Caucasus"]
    assert set(cauc) == _FULL_KEYS
    assert cauc["proj"] == "tmerc"
    assert cauc["lon_0"] == 33
    assert cauc["k_0"] == 0.9996
    assert cauc["proj4"].startswith("+proj=tmerc")
    assert "+lon_0=33" in cauc["proj4"]


def test_to_json_roundtrip():
    reg = build_registry()
    assert json.loads(to_json(reg)) == reg


def test_to_yaml_roundtrip():
    reg = build_registry()
    loaded = yaml.safe_load(to_yaml(reg))
    assert loaded == reg


def test_to_python_executes():
    reg = build_registry()
    ns: dict = {}
    exec(to_python(reg), ns)  # noqa: S102 - generated, trusted content
    maps_list = ns["MAPS"]
    by_name = ns["MAPS_BY_NAME"]
    assert len(maps_list) == len(reg)
    assert {m.name for m in maps_list} == set(reg)
    cauc = by_name["Caucasus"]
    assert cauc.lon_0 == reg["Caucasus"]["lon_0"]
    assert cauc.x_0 == reg["Caucasus"]["x_0"]
    # the computed proj4 property must match the source-of-truth proj4 exactly
    assert cauc.proj4 == reg["Caucasus"]["proj4"]


def test_to_markdown_has_table_and_proj():
    md = to_markdown(build_registry())
    assert "| Map |" in md
    assert "## Full PROJ strings" in md
    assert "Caucasus" in md


def test_generate_writes_all_formats(tmp_path):
    paths = generate(tmp_path)
    names = {p.name for p in paths}
    assert names == {"maps.yaml", "maps.json", "maps.md", "maps.py"}
    for p in paths:
        assert p.exists() and p.stat().st_size > 0
