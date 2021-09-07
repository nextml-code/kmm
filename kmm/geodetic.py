import pandas as pd
from sweref99 import projections


tm = projections.make_transverse_mercator("SWEREF_99_TM")


def geodetic(positions: pd.DataFrame):
    yx = positions.apply(
        lambda row: (tm.grid_to_geodetic(row["x_sweref"], row["y_sweref"])),
        axis="columns",
        result_type="reduce",
    )
    return (
        positions
        .assign(longitude=yx.map(lambda yx: yx[1]))
        .assign(latitude=yx.map(lambda yx: yx[0]))
    )


def test_geodetic():
    from kmm.kmm2 import kmm2

    df = kmm2("tests/ascending_B.kmm2")
    df = geodetic(df)
    assert ((df["latitude"] < 68) & (df["latitude"] > 55)).all()
    assert ((df["longitude"] < 25) & (df["longitude"] > 7)).all()
