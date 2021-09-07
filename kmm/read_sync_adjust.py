from pathlib import Path
from pydantic import validate_arguments

import kmm


@validate_arguments
def read_sync_adjust(
    path: Path,
    header_path: Path,
    adjust: int = kmm.PositionAdjustment.WIRE_CAMERA,
    geodetic: bool = True,
):
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

    df = kmm.read_raw(path)
    df = kmm.sync_frame_index(df, header_path)
    if adjust == kmm.PositionAdjustment.WIRE_CAMERA:
        df = kmm.camera_positions(df, header_path)
    if geodetic:
        df = kmm.geodetic(df)

    return df


def test_read_kmm():
    df = read_sync_adjust("tests/ascending_B.kmm", "tests/ascending_B.hdr")
    assert len(df) > 0


def test_read_kmm2():
    df = read_sync_adjust("tests/ascending_B.kmm2", "tests/ascending_B.hdr")
    assert len(df) > 0


def test_empty_kmm():
    df = read_sync_adjust("tests/empty.kmm", "tests/empty.hdr")
    assert len(df) == 0


def test_empty_kmm2():
    df = read_sync_adjust("tests/empty.kmm2", "tests/empty.hdr")
    assert len(df) == 0
