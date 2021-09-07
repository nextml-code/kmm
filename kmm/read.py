from pathlib import Path
from pydantic import validate_arguments

from kmm.kmm import kmm
from kmm.kmm2 import kmm2
from kmm.camera_positions import camera_positions
from kmm.sync_frame_index import sync_frame_index


@validate_arguments
def read(path: Path, header_path: Path):
    """
    Used to load a kmm or kmm2 file as a pandas DataFrame.

    Example:

    .. code-block:: python

        from pathlib import Path
        import kmm

        path = Path("...")
        header_path = Path("...")

        df = kmm.read(path, header_path)

    """

    if path.suffix == ".kmm":
        df = kmm(path)
    elif path.suffix == ".kmm2":
        df = kmm2(path)
    else:
        raise ValueError(f"Unable to parse file type {path.suffix}")

    if header_path is not None:
        df = camera_positions(df, header_path)
        df = sync_frame_index(df, header_path)

    return df


def test_empty_kmm():
    df = read("tests/empty.kmm", "tests/empty.hdr")
    assert len(df) == 0


def test_empty_kmm2():
    df = read("tests/empty.kmm2", "tests/empty.hdr")
    assert len(df) == 0


def test_camera_positions_kmm():
    df = kmm("tests/ascending_B.kmm")
    df_calibrated = read("tests/ascending_B.kmm", "tests/ascending_B.hdr")
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8


def test_camera_positions_kmm2():
    df = kmm2("tests/ascending_B.kmm2")
    df_calibrated = read("tests/ascending_B.kmm2", "tests/ascending_B.hdr")
    assert df_calibrated["meter"].iloc[0] == df["meter"].iloc[0] - 8
