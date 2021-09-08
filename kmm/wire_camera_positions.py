import pandas as pd
from pydantic import validate_arguments

from kmm import CarDirection


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def wire_camera_positions(positions: pd.DataFrame, direction: CarDirection):
    ascending = kmm_ascending(positions)

    if (
        (direction == CarDirection.A and ascending)
        or (direction == CarDirection.B and not ascending)
    ):
        correction = -8

    elif (
        (direction == CarDirection.A and not ascending)
        or (direction == CarDirection.B and ascending)
    ):
        correction = 8

    else:
        raise ValueError

    return (
        positions
        .assign(meter=lambda df: df["meter"] + correction)
    )


def kmm_ascending(positions):
    total_meter = positions["kilometer"] * 1000 + positions["meter"]
    diff = total_meter.values[:-1] - total_meter.values[1:]
    descending = (diff < 0).mean()
    ascending = (diff > 0).mean()

    if descending < 0.9 and ascending < 0.9:
        raise ValueError("Unable to determine ascending/descending kmm numbers")

    else:
        return ascending > 0.9


def test_camera_positions_kmm():
    from kmm import kmm, Header

    df = kmm("tests/ascending_B.kmm")
    header = Header.from_path("tests/ascending_B.hdr")
    df_calibrated = wire_camera_positions(df, header.car_direction)
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8


def test_camera_positions_kmm2():
    from kmm import kmm2, Header

    df = kmm2("tests/ascending_B.kmm2")
    header = Header.from_path("tests/ascending_B.hdr")
    df_calibrated = wire_camera_positions(df, header.car_direction)
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8
