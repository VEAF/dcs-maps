"""Shared test fixtures."""

import pytest

import dcs_coords.maps as maps_mod


@pytest.fixture(autouse=True)
def _reset_maps_cache():
    """Clear the registry cache after each test.

    Some tests monkeypatch ``maps.MAPS_YAML`` to a temp file; reloading on teardown
    guarantees the next test reads the real ``maps.yaml`` again.
    """
    yield
    maps_mod.reload()
