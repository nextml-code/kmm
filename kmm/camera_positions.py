import re
from pathlib import Path
import pandas as pd


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
    return re.search(
        r"CarDirection = \"(.*)\"",
        header_path.read_text(),
    ).group(1)
