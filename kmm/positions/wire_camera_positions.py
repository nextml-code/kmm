import numpy as np
from pydantic import validate_arguments

from kmm import CarDirection
from kmm.positions.positions import Positions


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def wire_camera_positions(positions: Positions, car_direction: CarDirection):

    if car_direction == CarDirection.A:
        corrections = kmm_directions(positions.dataframe) * -8
    elif car_direction == CarDirection.B:
        corrections = kmm_directions(positions.dataframe) * 8
    else:
        raise ValueError(car_direction)

    return positions.replace(
        dataframe=(
            positions.dataframe
            .assign(meter=lambda df: df["meter"] + corrections)
        )
    )


def kmm_directions(df):

    total_meter = (df["kilometer"] * 1000 + df["meter"]).values

    track_section_changes = np.argwhere(np.concatenate([
        np.array([True]),
        df["track_section"].values[1:] != df["track_section"].values[:-1],
    ])).squeeze(1).tolist() + [len(df)]

    return np.concatenate([
        (
            np.ones(to_index - from_index, dtype=np.uint8)
            * kmm_direction(total_meter[from_index: to_index])
        )
        for from_index, to_index in zip(
            track_section_changes[:-1],
            track_section_changes[1:],
        )
    ])


def kmm_direction(total_meter):
    diffs = np.clip(total_meter[1:] - total_meter[:-1], -1, 1)
    if len(diffs) >= 10 and (diffs > 0).mean() < 0.9 and (diffs < 0).mean() < 0.9:
        raise ValueError("Unable to determine direction of kmm numbers.", diffs)
    return int(np.sign(diffs.sum()))


def test_camera_positions_kmm():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm")
    header = Header.from_path("tests/ascending_B.hdr")
    positions_calibrated = wire_camera_positions(positions, header.car_direction)
    assert (
        positions_calibrated.dataframe["meter"].iloc[0]
        == positions.dataframe["meter"].iloc[0] + 8
    )


def test_camera_positions_kmm2():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm2")
    header = Header.from_path("tests/ascending_B.hdr")
    positions_calibrated = wire_camera_positions(positions, header.car_direction)
    assert (
        positions_calibrated.dataframe["meter"].iloc[0]
        == positions.dataframe["meter"].iloc[0] + 8
    )
