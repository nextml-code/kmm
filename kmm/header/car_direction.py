import re
from xml.etree import ElementTree

import kmm


def car_direction(tree: ElementTree):

    root = tree.getroot()
    start_tags = [
        child.text
        for child in root
        if child.tag == "Start"
    ]

    if len(start_tags) != 1:
        raise ValueError(f"Expected 1 'Start' tag in header, found {len(start_tags)}")

    start_tag = start_tags[0]
    car_direction = re.search(
        r"CarDirection = \"(.*)\"",
        start_tag,
    )
    if car_direction is None:
        raise ValueError("""Did not find a "CarDirection" field under the Start tag.""")
    else:
        car_direction = car_direction.group(1)

    if not any(car_direction == item.value for item in kmm.CarDirection):
        raise ValueError(f"Unknown car direction {car_direction}")

    return kmm.CarDirection[car_direction]
