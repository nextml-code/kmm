from pathlib import Path
import pandas as pd
from pydantic import validate_arguments

import kmm


class Positions(kmm.FunctionalBase):

    dataframe: pd.DataFrame
    header_path: Path

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    @validate_arguments
    def from_paths(kmm_path: Path, header_path: Path):
        """
        Loads positions and metadata from kmm or kmm2 file and header file.
        """

        return Positions(
            dataframe=kmm.read_raw(kmm_path),
            header_path=header_path,
        )

    def sync_frame_index(self):
        return self.replace(
            dataframe=kmm.sync_frame_index(self.dataframe, self.header_path),
        )

    def adjust(self, adjustment: int):
        if adjustment == kmm.PositionAdjustment.WIRE_CAMERA:
            dataframe = kmm.camera_positions(self.dataframe, self.header_path)
        else:
            raise ValueError(f"Unknown adjustment option {adjustment}")
        return self.replace(dataframe=dataframe)

    def geodetic(self):
        return self.replace(dataframe=kmm.geodetic(self.dataframe))


def test_read_kmm():
    positions = (
        Positions
        .from_paths("tests/ascending_B.kmm", "tests/ascending_B.hdr")
        .sync_frame_index()
        .adjust(kmm.PositionAdjustment.WIRE_CAMERA)
        .geodetic()
    )
    assert len(positions.dataframe) > 0


def test_read_kmm2():
    positions = (
        Positions
        .from_paths("tests/ascending_B.kmm2", "tests/ascending_B.hdr")
        .sync_frame_index()
        .adjust(kmm.PositionAdjustment.WIRE_CAMERA)
        .geodetic()
    )
    assert len(positions.dataframe) > 0


def test_empty_kmm():
    positions = Positions.from_paths("tests/empty.kmm", "tests/empty.hdr")
    assert len(positions.dataframe) == 0


def test_empty_kmm2():
    positions = Positions.from_paths("tests/empty.kmm2", "tests/empty.hdr")
    assert len(positions.dataframe) == 0
