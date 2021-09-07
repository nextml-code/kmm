import re
from pathlib import Path
import pandas as pd
from xml.etree import ElementTree
from pydantic import validate_arguments


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def camera_positions(positions: pd.DataFrame, header_path: Path):
    ascending = kmm_ascending(positions)
    direction = car_direction(header_path)

    if (direction == "A" and ascending) or (direction == "B" and not ascending):
        correction = -8

    elif (direction == "A" and not ascending) or (direction == "B" and ascending):
        correction = 8

    else:
        raise ValueError

    return (
        positions
        .assign(meter=lambda df: df["meter"] + correction)
    )


def kmm_ascending(positions):
    total_meter = positions["kilometer"] * 1000 + positions["meter"]
    diff = total_meter.values[:-1] - total_meter.values[1:]
    descending = (diff < 0).mean()
    ascending = (diff > 0).mean()

    if descending < 0.9 and ascending < 0.9:
        raise ValueError("Unable to determine ascending/descending kmm numbers")

    else:
        return ascending > 0.9


def car_direction(header_path: Path):

    tree = ElementTree.parse(header_path)
    root = tree.getroot()
    start_tags = [
        child.text
        for child in root
        if child.tag == "Start"
    ]

    if len(start_tags) != 1:
        raise ValueError(f"Expected 1 'Start' tag in header file, found {len(start_tags)}")

    start_tag = start_tags[0]
    car_direction = re.search(
        r"CarDirection = \"(.*)\"",
        start_tag,
    ).group(1)

    if car_direction not in ["A", "B"]:
        raise ValueError(f"Unkown car direction {car_direction}")

    return car_direction


def test_camera_positions_kmm():
    from kmm.kmm import kmm

    df = kmm("tests/ascending_B.kmm")
    df_calibrated = camera_positions(df, "tests/ascending_B.hdr")
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8


def test_camera_positions_kmm2():
    from kmm.kmm2 import kmm2

    df = kmm2("tests/ascending_B.kmm2")
    df_calibrated = camera_positions(df, "tests/ascending_B.hdr")
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8
