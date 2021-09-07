import re
import numpy as np
import pandas as pd
from pathlib import Path
from pydantic import validate_arguments


pattern = re.compile(r".+\[.+\]")
pattern2 = re.compile(r"CMAST")


@validate_arguments
def kmm2(path: Path):

    skiprows = [
        index
        for index, line in enumerate(path.read_text(encoding="latin1").splitlines())
        if pattern.match(line) or pattern2.match(line)
    ]

    return pd.read_csv(
        path,
        skiprows=[0] + skiprows,
        delimiter="\t",
        encoding="latin1",
        names=[
            "code",
            "centimeter",
            "track_section",
            "kilometer",
            "meter",
            "track_lane",
            "1?",
            "2?",
            "3?",
            "4?",
            "sweref99_tm_x",
            "sweref99_tm_y",
            "contact_wire_material",
            "rail_model",
            "sliper_model",
            "between_stations",
            "5?",
            "6?",
            "7?",
            "8?",
            "max_speed",
        ],
        dtype=dict(
            centimeter=np.int64,
            track_section=str,
            kilometer=np.int32,
            meter=np.int32,
            track_lane=str,
            sweref99_tm_x=np.float32,
            sweref99_tm_y=np.float32,
        ),
        low_memory=False,
    )


def test_patterns():
    assert pattern.match("Västerås central [Vå]")
    assert pattern2.match("CMAST   281-2B")
