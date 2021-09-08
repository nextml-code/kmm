import re
from xml.etree import ElementTree


def position_sync(tree: ElementTree):

    root = tree.getroot()
    sync_tags = [
        child.text
        for child in root
        if child.tag == "Sync"
    ]

    if len(sync_tags) == 0:
        raise ValueError("Did not find a sync tag in header.")

    sync_tag = sync_tags[0]

    position = int(re.search(
        r"Position = \"(\d*)\"",
        sync_tag,
    ).group(1))

    sync = int(re.search(
        r"Sync = \"(\d*)\"",
        sync_tag,
    ).group(1))

    return position, sync
