"""Calibration tests: recover the published constants from synthetic points.

Points are synthesised from the seeded PROJ string of each map, then fed back
into the calibrator. The recovered ``lon_0`` and offsets must match, and the
residual must be ~0. This validates the calibration algorithm itself (the
projection correctness is checked against an external reference in
``test_known_maps.test_caucasus_reference``).
"""

import pytest
from pyproj import CRS, Transformer

from dcs_coords.calibrate import calibrate_from_points
from dcs_coords.ingest import Point
from dcs_coords.maps import proj_string


def _synthesize(map_name: str) -> list[Point]:
    crs = CRS.from_proj4(proj_string(map_name))
    t = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    pts = []
    for x in range(-200_000, 200_001, 80_000):  # North
        for y in range(-200_000, 200_001, 80_000):  # East
            # inverse: (easting=y, northing=x) -> (lon, lat)
            lon, lat = t.transform(y, x, direction="INVERSE")
            pts.append(Point(x=x, y=y, lat=lat, lon=lon))
    return pts


@pytest.mark.parametrize(
    "map_name,lon_0",
    [("Caucasus", 33), ("Syria", 39), ("PersianGulf", 57), ("Nevada", -117), ("TheChannel", 3)],
)
def test_recover_lon0_and_residual(map_name, lon_0):
    calib = calibrate_from_points(map_name, _synthesize(map_name))
    assert calib.lon_0 == lon_0
    assert calib.residual_max_m < 0.01  # sub-centimetre


def test_recover_caucasus_offsets():
    calib = calibrate_from_points("Caucasus", _synthesize("Caucasus"))
    # Published Caucasus offsets (essentially integers).
    assert calib.x_0 == pytest.approx(-99517.0, abs=0.5)
    assert calib.y_0 == pytest.approx(-4998115.0, abs=0.5)


def test_too_few_points():
    with pytest.raises(ValueError):
        calibrate_from_points("Caucasus", _synthesize("Caucasus")[:2])
