from pathlib import Path
from xml.etree import ElementTree
from pydantic import validate_arguments

import kmm


class Header(kmm.FunctionalBase):
    car_direction: kmm.CarDirection
    position: int
    sync: int

    @staticmethod
    @validate_arguments
    def from_path(path: Path):
        """
        Loads header data from .hdr file.
        """
        tree = ElementTree.parse(path)
        position, sync = kmm.header.position_sync(tree)
        return Header(
            position=position,
            sync=sync,
            car_direction=kmm.header.car_direction(tree),
        )


def test_header():
    Header.from_path("tests/ascending_B.hdr")


def test_empty_header():
    Header.from_path("tests/empty.hdr")
