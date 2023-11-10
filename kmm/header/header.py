from pathlib import Path
from xml.etree import ElementTree

from pydantic import validate_arguments

import kmm


class Header(kmm.FunctionalBase):
    car_direction: kmm.CarDirection
    position: int
    sync: int

    @staticmethod
    @validate_arguments
    def from_path(path: Path, raise_on_malformed_data: bool = True):
        """
        Loads header data from .hdr file.
        """
        try:
            tree = ElementTree.parse(path)
        except ElementTree.ParseError:
            if raise_on_malformed_data:
                raise ValueError("Unable to parse header file, invalid XML.")
            tree = attempt_to_patch_xml(path)

        position, sync = kmm.header.position_sync(tree)
        return Header(
            position=position,
            sync=sync,
            car_direction=kmm.header.car_direction(tree),
        )


def attempt_to_patch_xml(path: Path):
    """
    Attempts to patch a broken header file by adding missing end tags.
    """
    lines = path.read_text().splitlines()
    start_tags = []
    for line in lines:
        if line.startswith("</") and line.endswith(">"):
            try:
                index = max(
                    i
                    for i, start_tag in enumerate(start_tags)
                    if start_tag == line[2:-1]
                )
            except ValueError:
                raise ElementTree.ParseError(f"Missing start tag for {line}")
            start_tags.pop(index)
        elif line.startswith("<") and line.endswith(">") and not line.startswith("<?"):
            start_tags.append(line[1:-1])
    for start_tag in start_tags[::-1]:
        lines.append(f"</{start_tag}>")
    try:
        return ElementTree.ElementTree(ElementTree.fromstring("\n".join(lines)))
    except ElementTree.ParseError as e:
        raise ValueError("Unable to parse header file, invalid XML.") from e


def test_header():
    Header.from_path("tests/ascending_B.hdr")


def test_empty_header():
    Header.from_path("tests/empty.hdr")
