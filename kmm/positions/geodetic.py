from sweref99 import projections

from kmm.positions.positions import Positions


tm = projections.make_transverse_mercator("SWEREF_99_TM")


def geodetic(positions: Positions):
    dataframe = positions.dataframe
    if len(dataframe) == 0:
        dataframe = dataframe.assign(longitude=[], latitude=[])
    else:
        latitude, longitude = zip(*[
            tm.grid_to_geodetic(coordinate.sweref99_tm_x, coordinate.sweref99_tm_y)
            for coordinate in dataframe[["sweref99_tm_x", "sweref99_tm_y"]].itertuples()
        ])
        dataframe = dataframe.assign(longitude=longitude, latitude=latitude)
    return positions.replace(dataframe=dataframe)


def test_geodetic():

    positions = Positions.from_path("tests/ascending_B.kmm2")
    df = geodetic(positions).dataframe
    assert ((df["latitude"] < 68) & (df["latitude"] > 55)).all()
    assert ((df["longitude"] < 25) & (df["longitude"] > 7)).all()
