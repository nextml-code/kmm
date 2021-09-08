from sweref99 import projections

from kmm.positions.positions import Positions


tm = projections.make_transverse_mercator("SWEREF_99_TM")


def geodetic(positions: Positions):
    dataframe = positions.dataframe
    if len(dataframe) == 0:
        dataframe = dataframe.assign(longitude=[], latitude=[])
    else:
        latitude, longitude = zip(*dataframe.apply(
            lambda row: (tm.grid_to_geodetic(row["sweref99_tm_x"], row["sweref99_tm_y"])),
            axis="columns",
            result_type="reduce",
        ))
        dataframe = dataframe.assign(longitude=longitude, latitude=latitude)
    return positions.replace(dataframe=dataframe)


def test_geodetic():

    positions = Positions.from_path("tests/ascending_B.kmm2")
    df = geodetic(positions).dataframe
    assert ((df["latitude"] < 68) & (df["latitude"] > 55)).all()
    assert ((df["longitude"] < 25) & (df["longitude"] > 7)).all()
