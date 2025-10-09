import re
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import validate_call

pattern = re.compile(r".+\[.+\]")
pattern2 = re.compile(r"CMAST")

expected_columns = [
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
    "northing",
    "easting",
    "contact_wire_material",
    "rail_model",
    "sliper_model",
    "between_stations",
    "5?",
    "6?",
    "7?",
    "8?",
    "max_speed",
    "datetime",
    "bearing",
    "linear_coordinate",
]
expected_dtypes = dict(
    centimeter=np.int64,
    track_section=str,
    kilometer=np.int32,
    meter=np.int32,
    track_lane=str,
    northing=np.float32,
    easting=np.float32,
)


@validate_call
def read_kmm2(
    path: Path, raise_on_malformed_data: bool = True, replace_commas: bool = True
):
    skiprows = [
        index
        for index, line in enumerate(path.read_text(encoding="latin1").splitlines())
        if pattern.match(line) or pattern2.match(line)
    ]
    with open(path, "r", encoding="latin1") as f:
        line = f.readline()
        if line.startswith("VER"):
            skiprows = [0] + skiprows
        elif raise_on_malformed_data and not line.startswith("POS"):
            raise ValueError("Malformed data, first line is not POS or VER")

    try:
        if replace_commas:
            with open(path, "r", encoding="latin1") as f:
                content = f.read()
            content = content.replace(",", ".")
            file_obj = StringIO(content)
        else:
            file_obj = path

        try:
            parser_kwargs = dict(
                sep="\t",
                encoding="latin1" if not replace_commas else None,
                header=None,
                skiprows=skiprows,
                low_memory=False,
            )
            n_columns = len(pd.read_csv(file_obj, **parser_kwargs).columns)

            # Reset file pointer to beginning for StringIO objects
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)

            if n_columns > len(expected_columns):
                columns = [f"{i+1}?" for i in range(len(expected_columns), n_columns)]
            elif n_columns < len(expected_columns):
                columns = expected_columns[:n_columns]
            else:
                columns = expected_columns

            return pd.read_csv(
                file_obj,
                **parser_kwargs,
                names=columns,
                dtype=expected_dtypes,
            )
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=expected_columns)
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise ValueError("Unable to parse kmm2 file, invalid csv.") from e


def test_patterns():
    assert pattern.match("Västerås central [Vå]")
    assert pattern2.match("CMAST   281-2B")


def test_extra_columns():
    read_kmm2(Path("tests/extra_columns.kmm2"))
