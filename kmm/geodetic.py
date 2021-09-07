import pandas as pd
from sweref99 import projections


tm = projections.make_transverse_mercator("SWEREF_99_TM")


def geodetic(positions: pd.DataFrame):
    if len(positions) == 0:
        positions = positions.assign(longitude=[], latitude=[])
    else:
        latitude, longitude = zip(*positions.apply(
            lambda row: (tm.grid_to_geodetic(row["sweref99_tm_x"], row["sweref99_tm_y"])),
            axis="columns",
            result_type="reduce",
        ))
        positions = positions.assign(longitude=longitude, latitude=latitude)
    return positions


def test_geodetic():
    from kmm.kmm2 import kmm2

    df = kmm2("tests/ascending_B.kmm2")
    df = geodetic(df)
    assert ((df["latitude"] < 68) & (df["latitude"] > 55)).all()
    assert ((df["longitude"] < 25) & (df["longitude"] > 7)).all()
