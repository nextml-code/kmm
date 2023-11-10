from pathlib import Path

import pandas as pd
from pydantic import validate_arguments

import kmm
from kmm.header.header import Header


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
        if path.suffix == ".kmm":
            dataframe = kmm.positions.read_kmm(path)
        elif path.suffix == ".kmm2":
            dataframe = kmm.positions.read_kmm2(path)
        else:
            raise ValueError(f"Unable to parse file type {path.suffix}")

        return Positions(dataframe=dataframe)

    @staticmethod
    @validate_arguments
    def read_sync_adjust(
        kmm_path: Path,
        header_path: Path,
        adjustment: kmm.PositionAdjustment = kmm.PositionAdjustment.WIRE_CAMERA,
        raise_on_malformed_data: bool = True,
    ):
        """
        Loads positions from .kmm or .kmm2 file + .hdr file, then performs
        frame index sync, position adjustment and geodetic coordinate transformation.
        """
        header = kmm.Header.from_path(header_path, raise_on_malformed_data)
        return (
            Positions.from_path(kmm_path)
            .sync_frame_index(header, adjustment, raise_on_malformed_data)
            .geodetic()
        )

    @validate_arguments
    def sync_frame_index(
        self,
        header: Header,
        adjustment: kmm.PositionAdjustment,
        raise_on_malformed_data: bool = True,
    ):
        return kmm.positions.sync_frame_index(
            self, header, adjustment, raise_on_malformed_data
        )

    def geodetic(self):
        return kmm.positions.geodetic(self)


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
