from pathlib import Path
from pydantic import validate_arguments

from kmm.positions import kmm, kmm2


@validate_arguments
def read_raw(path: Path):
    """
    Used to load a kmm or kmm2 file as a pandas DataFrame.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kmm

        path = Path("...")
        df = kmm.positions.read_raw(path)

    """
    if path.suffix == ".kmm":
        df = kmm(path)
    elif path.suffix == ".kmm2":
        df = kmm2(path)
    else:
        raise ValueError(f"Unable to parse file type {path.suffix}")

    return df
