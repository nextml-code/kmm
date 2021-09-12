import numpy as np
from pydantic import validate_arguments

from kmm import CarDirection
from kmm.positions.positions import Positions
from kmm.header.header import Header


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def sync_frame_index(positions: Positions, header: Header):

    frame_index = (
        (
            positions.dataframe["centimeter"].values
            + header.position
            - header.sync
        ) / 10
    ).astype(int)
    pad = np.zeros(8)
    pad.fill(np.nan)

    if header.car_direction == CarDirection.A:
        frame_index = np.concatenate([pad, frame_index[8:]])
    elif header.car_direction == CarDirection.B:
        frame_index = np.concatenate([frame_index[:-8], pad])
    else:
        raise ValueError(header.car_direction)

    return positions.replace(
        dataframe=positions.dataframe.assign(frame_index=frame_index)
    )


def test_sync_frame_index_kmm():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm")
    header = Header.from_path("tests/ascending_B.hdr")
    assert (
        sync_frame_index(positions, header)
        .dataframe["frame_index"].iloc[0] == 659
    )


def test_sync_frame_index_kmm2():
    from kmm import Header

    positions = Positions.from_path("tests/ascending_B.kmm2")
    header = Header.from_path("tests/ascending_B.hdr")
    assert (
        sync_frame_index(positions, header)
        .dataframe["frame_index"].iloc[0] == -808
    )
