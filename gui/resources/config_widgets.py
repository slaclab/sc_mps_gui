from itertools import groupby
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QLabel)
from pydm import Display


def channel_range(channels):
    """Takes a list of channels (AnalogChannel, DigitalChannel, or
    DigitalOutChannel) and returns ranges of numbers covered."""
    nums = sorted([ch.number for ch in channels])
    ranges = []
    for _, r in groupby(enumerate(nums), lambda e: e[1] - e[0]):
        r = list(r)
        if len(r) == 1:
            ranges.append((r[0][1], None))
        elif len(r) == 2:
            ranges.append((r[0][1], None))
            ranges.append((r[-1][1], None))
        else:
            ranges.append((r[0][1], r[-1][1]))

    return ", ".join([str(x) if not y else f"{x}-{y}" for x, y in ranges])


class ConfDef(Display):
    """ConfDef is the default widget/display for the Configure tab. It
    inherits from Display rather than QWidget, so that it can be opened
    with a PyDMEmbeddedDisplay initially."""
    def __init__(self, parent=None, **kw):
        super(ConfDef, self).__init__(parent=parent)
        self.setStyleSheet("font-weight: bold; font-size: 15pt")

        lyt = QVBoxLayout()
        self.setLayout(lyt)

        lbl = QLabel("Select Device(s) to Configure")
        lbl.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lyt.addWidget(lbl)

        lbl = QLabel("Supported Device Types:\n- BPMS")
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lyt.addWidget(lbl)

    def set_devices(self, **kw):
        pass

    def add_device(self, **kw):
        pass

    def remove_devices(self, **kw):
        pass


class ConfErr(QWidget):
    """ConfErr is the widget for the Configure tab that displays when an
    error relating to device selection occurs. This is typically when
    multiple devices of differing types are selected."""
    def __init__(self, parent=None, **kw):
        super(ConfErr, self).__init__(parent=parent)
        self.setStyleSheet("font-weight: bold; font-size: 15pt")

        lyt = QVBoxLayout()
        self.setLayout(lyt)

        lbl = QLabel("ERROR:")
        lbl.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        lyt.addWidget(lbl)

        lbl = QLabel("Select a supported Device Type:\n- BPMS\n\n" +
                     "~ or ~\n\nMultiple Types of Devices Selected\n" +
                     "Select devices of the same tpe to configure them all at once.")
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        lyt.addWidget(lbl)

    def set_devices(self, **kw):
        pass

    def add_device(self, **kw):
        pass

    def remove_devices(self, **kw):
        pass
