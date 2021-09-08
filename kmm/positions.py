from pathlib import Path
import pandas as pd
from pydantic import validate_arguments

import kmm


class Positions(kmm.FunctionalBase):

    dataframe: pd.DataFrame

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    @validate_arguments
    def from_path(path: Path):
        """
        Loads positions from .kmm or .kmm2 file.
        """
        return Positions(dataframe=kmm.read_raw(path))

    @staticmethod
    @validate_arguments
    def read_sync_adjust(
        kmm_path: Path,
        header_path: Path,
        adjustment: int = kmm.ADJUST_WIRE_CAMERA,
    ):
        """
        Loads positions from .kmm or .kmm2 file + .hdr file, then performs
        frame index sync, position adjustment and geodetic coordinate transformation.
        .
        """
        header = kmm.Header.from_path(header_path)
        return (
            Positions.from_path(kmm_path)
            .sync_frame_index(header)
            .adjust(adjustment, header)
            .geodetic()
        )

    def sync_frame_index(self, header):
        return self.replace(
            dataframe=self.dataframe.assign(
                frame_index=(
                    (
                        self.dataframe["centimeter"]
                        + header.position
                        - header.sync
                    ) / 10
                ).astype(int)
            )
        )

    def adjust(self, adjustment: int, header):
        if adjustment == kmm.ADJUST_WIRE_CAMERA:
            dataframe = kmm.wire_camera_positions(self.dataframe, header.car_direction)
        else:
            raise ValueError(f"Unknown adjustment option {adjustment}")
        return self.replace(dataframe=dataframe)

    def geodetic(self):
        return self.replace(dataframe=kmm.geodetic(self.dataframe))


def test_read_kmm():
    positions = Positions.read_sync_adjust(
        "tests/ascending_B.kmm", "tests/ascending_B.hdr"
    )
    assert len(positions.dataframe) > 0


def test_read_kmm2():
    positions = Positions.read_sync_adjust(
        "tests/ascending_B.kmm2", "tests/ascending_B.hdr"
    )
    assert len(positions.dataframe) > 0


def test_empty_kmm():
    positions = Positions.from_path("tests/empty.kmm")
    assert len(positions.dataframe) == 0


def test_empty_kmm2():
    positions = Positions.from_path("tests/empty.kmm2")
    assert len(positions.dataframe) == 0
