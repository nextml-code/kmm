import numpy as np
from pydantic import validate_arguments

from kmm import CarDirection, PositionAdjustment
from kmm.positions.positions import Positions
from kmm.header.header import Header


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def sync_frame_index(positions: Positions, header: Header, adjustment: PositionAdjustment):

    validate_meter_increments(positions)
    frame_index = (
        (
            positions.dataframe["centimeter"].values
            + header.position
            - header.sync
        ) / 10
    ).astype(int)

    if header.car_direction == CarDirection.A:
        dataframe = (
            positions.dataframe
            .iloc[adjustment:]
            .assign(frame_index=frame_index[adjustment:])
        )
    elif header.car_direction == CarDirection.B:
        dataframe = (
            positions.dataframe
            .iloc[:-adjustment]
            .assign(frame_index=frame_index[:-adjustment])
        )
    else:
        raise ValueError(header.car_direction)

    return positions.replace(dataframe=dataframe)


def validate_meter_increments(positions):
    for (track_section, kilometer), group in (
        positions.dataframe
        .groupby(["track_section", "kilometer"])
    ):
        diffs = np.sign(group["meter"].values[1:] - group["meter"].values[:-1])
        if len(diffs) >= 10 and (diffs > 0).mean() < 0.9 and (diffs < 0).mean() < 0.9:
            raise ValueError(
                f"Inconsistent directions at track_section {track_section}, kilometer {kilometer}."
            )


def test_sync_frame_index_kmm():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm")
    header = Header.from_path("tests/ascending_B.hdr")
    assert (
        sync_frame_index(positions, header, PositionAdjustment.WIRE_CAMERA)
        .dataframe["frame_index"].iloc[0] == 659
    )


def test_sync_frame_index_kmm2():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm2")
    header = Header.from_path("tests/ascending_B.hdr")
    assert (
        sync_frame_index(positions, header, PositionAdjustment.WIRE_CAMERA)
        .dataframe["frame_index"].iloc[0] == -808
    )
