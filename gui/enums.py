from enum import Enum
from qtpy.QtGui import (QBrush, QColor)


class DevThr(str, Enum):
    """Enum used for the Threshold Button in the Selection Details."""
    BPMS = "BPM"
    TORO = "CHRG"
    BLM = "I0_LOSS"
    BACT = "I0_BACT"


class Statuses(Enum):
    RED = (3, (255, 0, 0))          # Red:          Major Alarm
    YEL = (2, (235, 235, 0))        # Yellow:       Minor Alarm
    MAG = (1, (235, 0, 235))        # Magenta:      Error
    GRN = (0, (0, 235, 0))          # Green:        No Alarm
    WHT = (-1, (255, 255, 255))     # White:        Disconnected
    BGD = (-2, (0, 0, 0, 165))      # Background:   Table Background

    def num(self) -> int:
        return self.value[0]

    def rgb(self) -> tuple:
        return self.value[1]

    def brush(self) -> QBrush:
        return QBrush(QColor(*self.rgb()))

    def faulted(self) -> bool:
        return self.num() > 0

    def error(self) -> bool:
        return abs(self.num()) == 1

    @classmethod
    def max(cls) -> int:
        return cls.RED.num()
