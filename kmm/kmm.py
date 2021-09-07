import numpy as np
import pandas as pd
from pathlib import Path
from pydantic import validate_arguments


@validate_arguments
def kmm(path: Path):
    return pd.read_csv(
        path,
        sep="\t",
        encoding="latin1",
        names=[
            "centimeter",
            "track_section",
            "kilometer",
            "meter",
            "track_lane",
            "1?",
            "2?",
            "3?",
            "4?",
            "5?",
            "sweref99_tm_x",
            "sweref99_tm_y",
            "8?",
            "9?",
        ],
        dtype=dict(
            track_section=str,
            kilometer=np.int32,
            meter=np.int32,
            track_lane=str,
            sweref99_tm_x=np.float32,
            sweref99_tm_y=np.float32,
        ),
    )
