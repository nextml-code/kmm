import numpy as np
from pydantic import validate_arguments

from kmm import CarDirection, PositionAdjustment
from kmm.header.header import Header
from kmm.positions.positions import Positions


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def sync_frame_index(
    positions: Positions,
    header: Header,
    adjustment: PositionAdjustment,
    raise_on_malformed_data: bool = True,
):
    if raise_on_malformed_data:
        validate_meter_increments(positions)
    frame_index = (
        (positions.dataframe["centimeter"].values + header.position - header.sync) / 10
    ).astype(int)

    if header.car_direction == CarDirection.A:
        dataframe = positions.dataframe.iloc[:-adjustment].assign(
            frame_index=frame_index[adjustment:]
        )
    elif header.car_direction == CarDirection.B:
        dataframe = positions.dataframe.iloc[adjustment:].assign(
            frame_index=frame_index[:-adjustment]
        )
    else:
        raise ValueError(f"Unsupported car direction {header.car_direction}")

    return positions.replace(
        dataframe=dataframe.assign(car_direction=header.car_direction)
    )


def validate_meter_increments(positions):
    for (track_section, kilometer), group in positions.dataframe.groupby(
        ["track_section", "kilometer"]
    ):
        diffs = np.sign(group["meter"].values[1:] - group["meter"].values[:-1])
        if len(diffs) >= 10 and (diffs > 0).mean() < 0.9 and (diffs < 0).mean() < 0.9:
            raise ValueError(
                f"Inconsistent directions at track_section {track_section}, kilometer {kilometer}."
            )


def test_sync_frame_index_ascending_B_kmm():
    from kmm import Header

    synced = sync_frame_index(
        Positions.from_path("tests/ascending_B.kmm"),
        Header.from_path("tests/ascending_B.hdr"),
        PositionAdjustment.WIRE_CAMERA,
    ).dataframe
    assert synced[synced["frame_index"] == 675]["kilometer"].values[0] == 292
    assert synced[synced["frame_index"] == 675]["meter"].values[0] == 737 + 8


def test_sync_frame_index_ascending_B_kmm2():
    from kmm import Header

    synced = sync_frame_index(
        Positions.from_path("tests/ascending_B.kmm2"),
        Header.from_path("tests/ascending_B.hdr"),
        PositionAdjustment.WIRE_CAMERA,
    ).dataframe
    assert synced[synced["frame_index"] == 5]["kilometer"].values[0] == 292
    assert synced[synced["frame_index"] == 5]["meter"].values[0] == 802 + 8


def test_sync_frame_index_ascending_A():
    from kmm import Header

    synced = sync_frame_index(
        Positions.from_path("tests/ascending_A.kmm2"),
        Header.from_path("tests/ascending_A.hdr"),
        PositionAdjustment.WIRE_CAMERA,
    ).dataframe
    assert synced[synced["frame_index"] == 8]["kilometer"].values[0] == 534
    assert synced[synced["frame_index"] == 8]["meter"].values[0] == 336 - 8


def test_sync_frame_index_descending_A():
    from kmm import Header

    synced = sync_frame_index(
        Positions.from_path("tests/descending_A.kmm2"),
        Header.from_path("tests/descending_A.hdr"),
        PositionAdjustment.WIRE_CAMERA,
    ).dataframe
    assert synced[synced["frame_index"] == 1000]["kilometer"].values[0] == 57
    assert synced[synced["frame_index"] == 1000]["meter"].values[0] == 2 + 8
