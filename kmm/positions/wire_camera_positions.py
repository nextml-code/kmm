from pydantic import validate_arguments

from kmm import CarDirection
from kmm.positions.positions import Positions


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def wire_camera_positions(positions: Positions, direction: CarDirection):
    ascending = kmm_ascending(positions.dataframe)

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

    return positions.replace(
        dataframe=(
            positions.dataframe
            .assign(meter=lambda df: df["meter"] + correction)
        )
    )


def kmm_ascending(dataframe):
    total_meter = dataframe["kilometer"] * 1000 + dataframe["meter"]
    diff = total_meter.values[:-1] - total_meter.values[1:]
    descending = (diff < 0).mean()
    ascending = (diff > 0).mean()

    if descending < 0.9 and ascending < 0.9:
        raise ValueError("Unable to determine ascending/descending kmm numbers")

    else:
        return ascending > 0.9


def test_camera_positions_kmm():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm")
    header = Header.from_path("tests/ascending_B.hdr")
    positions_calibrated = wire_camera_positions(positions, header.car_direction)
    assert (
        positions_calibrated.dataframe["meter"].iloc[0]
        == positions.dataframe["meter"].iloc[0] - 8
    )


def test_camera_positions_kmm2():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm2")
    header = Header.from_path("tests/ascending_B.hdr")
    positions_calibrated = wire_camera_positions(positions, header.car_direction)
    assert (
        positions_calibrated.dataframe["meter"].iloc[0]
        == positions.dataframe["meter"].iloc[0] - 8
    )
