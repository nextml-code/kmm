import numpy as np
from sweref99 import projections

from kmm.positions.positions import Positions

tm = projections.make_transverse_mercator("SWEREF_99_TM")


def geodetic(positions: Positions):
    dataframe = positions.dataframe
    if len(dataframe) == 0:
        dataframe = dataframe.assign(longitude=[], latitude=[])
    else:
        latitude, longitude = zip(
            *[
                tm.grid_to_geodetic(coordinate.northing, coordinate.easting)
                for coordinate in dataframe[["northing", "easting"]].itertuples()
            ]
        )
        dataframe = dataframe.assign(longitude=longitude, latitude=latitude)
    return positions.replace(dataframe=dataframe)


def test_geodetic():
    positions = Positions.from_path("tests/ascending_B.kmm2")
    df = geodetic(positions).dataframe
    assert ((df["latitude"] < 68) & (df["latitude"] > 55)).all()
    assert ((df["longitude"] < 25) & (df["longitude"] > 7)).all()


def test_sweref_library():
    lat, lon = 57.705918, 11.987286

    northing, easting = tm.geodetic_to_grid(lat, lon)

    lat2, lon2 = tm.grid_to_geodetic(northing, easting)

    assert np.allclose([lat, lon], [lat2, lon2])
