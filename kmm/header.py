import re
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
        position, sync = position_sync(tree)
        return Header(
            position=position,
            sync=sync,
            car_direction=car_direction(tree),
        )


def car_direction(tree: ElementTree):

    root = tree.getroot()
    start_tags = [
        child.text
        for child in root
        if child.tag == "Start"
    ]

    if len(start_tags) != 1:
        raise ValueError(f"Expected 1 'Start' tag in header, found {len(start_tags)}")

    start_tag = start_tags[0]
    car_direction = re.search(
        r"CarDirection = \"(.*)\"",
        start_tag,
    ).group(1)

    if not any(car_direction == item.value for item in kmm.CarDirection):
        raise ValueError(f"Unknown car direction {car_direction}")

    return kmm.CarDirection[car_direction]


def position_sync(tree: ElementTree):

    root = tree.getroot()
    sync_tags = [
        child.text
        for child in root
        if child.tag == "Sync"
    ]

    if len(sync_tags) == 0:
        raise ValueError("Did not find a sync tag in header.")

    sync_tag = sync_tags[0]

    position = int(re.search(
        r"Position = \"(\d*)\"",
        sync_tag,
    ).group(1))

    sync = int(re.search(
        r"Sync = \"(\d*)\"",
        sync_tag,
    ).group(1))

    return position, sync


def test_header():
    Header.from_path("tests/ascending_B.hdr")


def test_empty_header():
    Header.from_path("tests/empty.hdr")
