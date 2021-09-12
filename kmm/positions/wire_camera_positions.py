import numpy as np
from pydantic import validate_arguments
import pandas as pd

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
    records = list()
    for (track_section, kilometer), group in df.groupby(["track_section", "kilometer"]):
        diffs = np.sign(group["meter"].values[1:] - group["meter"].values[:-1])
        diffs = diffs[diffs != 0]
        if len(diffs) >= 10 and (diffs > 0).mean() < 0.9 and (diffs < 0).mean() < 0.9:
            raise ValueError(
                f"Inconsistent directions at track_section {track_section}, kilometer {kilometer}."
            )
        records.append(dict(
            track_section=track_section,
            kilometer=kilometer,
            direction=int(np.sign(diffs.sum())),
        ))
    return df.merge(
        pd.DataFrame.from_records(
            records,
            columns=["track_section", "kilometer", "direction"],
        ),
        on=["track_section", "kilometer"],
        how="left",
    )["direction"].values


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
