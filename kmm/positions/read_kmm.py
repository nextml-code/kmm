from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import validate_arguments


@validate_arguments
def read_kmm(path: Path, replace_commas: bool = True):
    try:
        if replace_commas:
            with open(path, "r", encoding="latin1") as f:
                content = f.read()
            content = content.replace(",", ".")
            file_obj = StringIO(content)
        else:
            file_obj = path
        return pd.read_csv(
            file_obj,
            sep="\t",
            encoding="latin1" if not replace_commas else None,
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
                "northing",
                "easting",
                "8?",
                "9?",
            ],
            dtype=dict(
                track_section=str,
                kilometer=np.int32,
                meter=np.int32,
                track_lane=str,
                northing=np.float32,
                easting=np.float32,
            ),
        )
    except Exception as e:
        raise ValueError("Unable to parse kmm2 file, invalid csv.") from e
