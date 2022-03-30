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
        raise ValueError("Did not find a Sync tag in header.")

    sync_tag = sync_tags[0]

    position = re.search(
        r"Position = \"(\d*)\"",
        sync_tag,
    )
    if position is not None:
        position = int(position.group(1))
    else:
        raise ValueError("""Did not find a "Position" field under the Sync tag.""")

    sync = re.search(
        r"Sync = \"(\d*)\"",
        sync_tag,
    )

    if sync is not None:
        sync = int(sync.group(1))
    else:
        raise ValueError("""Did not find a "Sync" field under the Sync tag.""")

    return position, sync
