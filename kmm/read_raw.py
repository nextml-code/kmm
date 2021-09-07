from pathlib import Path
from pydantic import validate_arguments

import kmm


@validate_arguments
def read_raw(path: Path):
    if path.suffix == ".kmm":
        df = kmm.kmm(path)
    elif path.suffix == ".kmm2":
        df = kmm.kmm2(path)
    else:
        raise ValueError(f"Unable to parse file type {path.suffix}")

    return df
