from enum import Enum


class PositionAdjustment(str, Enum):
    MEASURING_INSTRUMENT = 'measuring_instrument'
    WIRE_CAMERA = 'wire_camera'
