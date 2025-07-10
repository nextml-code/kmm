from pathlib import Path

import pandas as pd
from pydantic import ConfigDict, validate_call

import kmm
from kmm.header.header import Header


class Positions(kmm.FunctionalBase):
    dataframe: pd.DataFrame

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    @validate_call
    def from_path(
        path: Path,
        raise_on_malformed_data: bool = True,
        replace_commas: bool = True,
    ):
        """
        Loads positions from .kmm or .kmm2 file.
        """
        if path.suffix == ".kmm":
            dataframe = kmm.positions.read_kmm(path)
        elif path.suffix == ".kmm2":
            dataframe = kmm.positions.read_kmm2(
                path,
                raise_on_malformed_data=raise_on_malformed_data,
                replace_commas=replace_commas,
            )
        else:
            raise ValueError(f"Unable to parse file type {path.suffix}")

        return Positions(dataframe=dataframe)

    @staticmethod
    @validate_call
    def read_sync_adjust_from_header_path(
        header_path: Path,
        kmm2=True,
        raise_on_malformed_data: bool = True,
        replace_commas: bool = True,
    ):
        """
        Convenience method to load positions from a header file, assumes a kmm file in the same directory.
        If kmm2 is True, the method will load a kmm2 file, otherwise a kmm file.
        """
        kmm_stem = (
            header_path.stem.replace("owlsbtlpos", "").split("_2011T")[0] + "_2011T"
        )
        if kmm2:
            kmm_path = header_path.parent / f"{kmm_stem}.kmm2"
        else:
            kmm_path = header_path.parent / f"{kmm_stem}.kmm"
        return Positions.read_sync_adjust(
            kmm_path,
            header_path,
            raise_on_malformed_data=raise_on_malformed_data,
            replace_commas=replace_commas,
        )

    @staticmethod
    @validate_call
    def read_sync_adjust_from_measurement_name(
        measurement_name: str,
        input_dir: Path,
        kmm2: bool = True,
        raise_on_malformed_data: bool = True,
        replace_commas: bool = True,
    ):
        """
        Convenience method to load positions from a measurement name, assumes a kmm2 file and a header file in input_dir.
        """
        timestamp = "_".join(measurement_name.split("_")[:-1])
        part = measurement_name.split("_")[-1]
        if kmm2:
            kmm_path = input_dir / f"{timestamp}_2011T.kmm2"
        else:
            kmm_path = input_dir / f"{timestamp}_2011T.kmm"
        header_path = input_dir / f"owlsbtlpos{timestamp}_2011T{part}.hdr"
        return Positions.read_sync_adjust(
            kmm_path,
            header_path,
            raise_on_malformed_data=raise_on_malformed_data,
            replace_commas=replace_commas,
        )

    @staticmethod
    @validate_call
    def read_sync_adjust(
        kmm_path: Path,
        header_path: Path,
        adjustment: kmm.PositionAdjustment = kmm.PositionAdjustment.WIRE_CAMERA,
        raise_on_malformed_data: bool = True,
        replace_commas: bool = True,
    ):
        """
        Loads positions from .kmm or .kmm2 file + .hdr file, then performs
        frame index sync, position adjustment and geodetic coordinate transformation.
        """
        header = kmm.Header.from_path(header_path, raise_on_malformed_data)
        return (
            Positions.from_path(
                kmm_path,
                raise_on_malformed_data=raise_on_malformed_data,
                replace_commas=replace_commas,
            )
            .sync_frame_index(header, adjustment, raise_on_malformed_data)
            .geodetic()
        )

    @validate_call
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


def test_read_sync_adjust_from_header_path():
    positions = Positions.read_sync_adjust_from_header_path(
        "tests/owlsbtlpos20210819_165120_2011TA.hdr", kmm2=True
    )
    assert len(positions.dataframe) > 0


def test_read_sync_adjust_from_measurement_name():
    positions = Positions.read_sync_adjust_from_measurement_name(
        "20210819_165120_A", "tests"
    )
    assert len(positions.dataframe) > 0
