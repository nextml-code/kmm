import re
import pandas as pd
from pathlib import Path
from xml.etree import ElementTree
from pydantic import validate_arguments


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def sync_frame_index(positions: pd.DataFrame, header_path: Path):

    tree = ElementTree.parse(header_path)
    root = tree.getroot()
    sync_tags = [
        child.text
        for child in root
        if child.tag == "Sync"
    ]

    if len(sync_tags) == 0:
        raise ValueError("Did not find a sync tag.")

    sync_tag = sync_tags[0]

    position = int(re.search(
        r"Position = \"(\d*)\"",
        sync_tag,
    ).group(1))

    sync = int(re.search(
        r"Sync = \"(\d*)\"",
        sync_tag,
    ).group(1))

    return positions.assign(
        frame_index=(positions["centimeter"] + position - sync) / 10
    )


def test_sync_frame_index():
    from kmm.kmm2 import kmm2

    df = kmm2("tests/ascending_B.kmm2")
    df = sync_frame_index(df, "tests/ascending_B.hdr")
    assert (~df["frame_index"].isnull()).all()
