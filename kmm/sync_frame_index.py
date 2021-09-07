import re
import pandas as pd
from pathlib import Path
from xml.etree import ElementTree


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
