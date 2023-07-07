from qtpy.QtCore import Qt
from qtpy.QtWidgets import (QWidget, QVBoxLayout, QLabel)
from pydm import Display


class ConfDef(Display):
    """ConfDef is the default widget/display for the Configure tab. It
    inherits from Display rather than QWidget, so that it can be opened
    with a PyDMEmbeddedDisplay initially."""
    def __init__(self, parent=None):
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


class ConfErr(QWidget):
    """ConfErr is the widget for the Configure tab that displays when an
    error relating to device selection occurs. This is typically when
    multiple devices of differing types are selected."""
    def __init__(self, parent=None):
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
