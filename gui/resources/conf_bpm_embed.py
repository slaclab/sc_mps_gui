from json import dumps
from functools import partial
from epics import (PV, caget_many)
from epics.dbr import DBE_VALUE
from qtpy.QtCore import (Qt, Slot)
from qtpy.QtWidgets import (QWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout,
                            QMessageBox, QHeaderView, QLabel, QTableWidget)
from pydm import Display
from pydm.widgets import (PyDMLabel, PyDMByteIndicator)
from models_pkg.mps_model import MPSModel
from resources.multi_channel_widgets import (PyDMMultiLineEdit, PyDMMultiCheckbox)
from resources.config_widgets import channel_range


class ConfBPM(Display):
    cell_fill_dict = {0: "LN",
                      1: "CL",
                      2: "AC",
                      3: "CH",
                      4: "X_T0",
                      5: "Y_T0",
                      6: "TMIT_T0",
                      7: "TMIT_T1",
                      8: "TMIT_T2",
                      9: "TMIT_T3",
                      10: "TMIT_T4",
                      11: "TMIT_T5"}

    def __init__(self, parent=None, macros=None, devices=[], model=MPSModel):
        super(ConfBPM, self).__init__(parent=parent, macros=macros,
                                      ui_filename=__file__.replace(".py", ".ui"))
        self.mac = macros
        self.devices = devices
        self.model = model

        self.ui.multi_dev_tbl.setEditTriggers(QTableWidget.NoEditTriggers)

        hdr = self.ui.multi_dev_tbl.verticalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)
        hdr = self.ui.multi_dev_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        self.device_names = {d: self.model.name.getDeviceName(d) for d in self.devices}
        if len(self.devices) <= 1:
            self.populate_single(self.devices[0])
            return

        self.ui.single_dev_scroll.hide()

        self.ui.multi_dev_tbl.show()
        self.ui.multi_dev_tbl.setColumnCount(len(self.devices) + 1)

        self.populate_write_column()
        for col in range(1, self.ui.multi_dev_tbl.columnCount()):
            self.populate_column(col)

        hdr_lst = ["Set Value To"] + list(self.device_names.values())
        self.ui.multi_dev_tbl.setHorizontalHeaderLabels(hdr_lst)

    def add_device(self, device):
        self.devices.append(device)
        self.device_names[device] = self.model.name.getDeviceName(device)

        self.populate_column(len(self.devices))
        self.populate_write_column()

    def remove_device(self, device):
        if device not in self.devices:
            return

        ind = self.devices.index(device)
        del self.devices[ind]
        del self.device_names[device]
        self.ui.multi_dev_tbl.removeColumn(ind)

        if len(self.devices) == 1:
            self.populate_single(self.devices[0])
            return

        self.populate_write_column()

    def populate_single(self, device):
        self.ui.multi_dev_tbl.hide()
        self.ui.single_dev_scroll.show()

        sheet = (f'QFrame[objectName="slot_{device.card.slot_number}_frame"]'
                 + '{background-color: rgb(0, 0, 255);}')
        self.ui.single_dev_cntnt.setStyleSheet(sheet)

        for slot_num in range(1, 8):
            app_lbl = getattr(self.ui, f"app_{slot_num}_lbl")
            app_lbl.setText(self.rich_text_label("Application", "Slot Empty"))

            ch_lbl = getattr(self.ui, f"ch_{slot_num}_lbl")
            ch_lbl.setText(self.rich_text_label("Channel"))

        for card in device.card.crate.cards:
            app_lbl = getattr(self.ui, f"app_{card.slot_number}_lbl")
            app_lbl.setText(self.rich_text_label("Application", card.number))

            channels = channel_range(card.analog_channels
                                     + card.digital_channels
                                     + card.digital_out_channels)
            ch_lbl = getattr(self.ui, f"ch_{card.slot_number}_lbl")
            ch_lbl.setText(self.rich_text_label("Channel", channels))

        ln_text = self.rich_text_label("LN", device.card.link_node.lcls1_id)
        self.ui.link_node_lbl.setText(ln_text)
        self.ui.crate_loc_lbl.setText(device.card.crate.location)
        self.ui.cpu_lbl.setText(device.card.link_node.cpu)

        dev_name = self.device_names[device]
        self.ui.xorbit_embed.macros = dumps({"P": f"{dev_name}:X",
                                             "THR": "T0",
                                             "NUM": 0,
                                             "FORMAT": "DEFAULT"})
        self.ui.yorbit_embed.macros = dumps({"P": f"{dev_name}:Y",
                                             "THR": "T0",
                                             "NUM": 0,
                                             "FORMAT": "DEFAULT"})
        for i in range(6):
            tmit_embed = getattr(self.ui, f"tmit_thr{i}_embed")
            tmit_embed.macros = dumps({"P": f"{dev_name}:TMIT",
                                       "THR": f"T{i}",
                                       "NUM": i,
                                       "FORMAT": "DEFAULT"})

    def populate_write_column(self):
        for row in range(self.ui.multi_dev_tbl.rowCount()):
            if row < 4:
                item = QTableWidgetItem("-")
                item.setTextAlignment(Qt.AlignCenter)
                self.ui.multi_dev_tbl.setItem(row, 0, item)
                continue

            row_devs = []
            for dev in self.devices:
                dev_name = self.device_names[dev]
                pv = f"{dev_name}:{self.cell_fill_dict[row]}"
                row_devs.append(pv)

            wid = ConfWriteBPM(self.ui.multi_dev_tbl, row_devs)
            self.ui.multi_dev_tbl.setCellWidget(row, 0, wid)

    def populate_column(self, col):
        device = self.devices[col - 1]

        item = QTableWidgetItem(str(device.card.link_node.lcls1_id))
        item.setTextAlignment(Qt.AlignCenter)
        self.ui.multi_dev_tbl.setItem(0, col, item)

        item = QTableWidgetItem(device.card.crate.location)
        item.setTextAlignment(Qt.AlignCenter)
        self.ui.multi_dev_tbl.setItem(1, col, item)

        item = QTableWidgetItem(str(device.card.number))
        item.setTextAlignment(Qt.AlignCenter)
        self.ui.multi_dev_tbl.setItem(2, col, item)

        channels = channel_range(device.card.analog_channels
                                 + device.card.digital_channels
                                 + device.card.digital_out_channels)
        item = QTableWidgetItem(channels)
        item.setTextAlignment(Qt.AlignCenter)
        self.ui.multi_dev_tbl.setItem(3, col, item)

        for row in range(4, self.ui.multi_dev_tbl.rowCount()):
            dev_name = self.device_names[device]
            pv = f"{dev_name}:{self.cell_fill_dict[row]}"
            wid = ConfReadBPM(self.ui.multi_dev_tbl, pv)
            self.ui.multi_dev_tbl.setCellWidget(row, col, wid)

    @staticmethod
    def rich_text_label(label, content=""):
        return ('<html><head/><body><p><span style=" font-weight:600;">'
                + f'{label}:</span> {content}</p></body></html>')


class ConfReadBPM(QWidget):
    def __init__(self, parent, dev: str):
        super(ConfReadBPM, self).__init__(parent=parent)
        self.dev = dev
        self.slope_pv = f"{self.dev.rsplit('_', 1)[0]}_SS_RBV"
        self.main_lyt = QVBoxLayout()
        self.setLayout(self.main_lyt)

        self.make_row("Min")
        self.make_row("Max")

        self.slope = PV(self.slope_pv,
                        callback=self.order_thresholds,
                        auto_monitor=DBE_VALUE)

    def make_row(self, min_max: str):
        """Makes the Min/Max row of the Read-only widget."""
        lyt = QHBoxLayout()

        lbl = QLabel(min_max)
        lbl.setFixedSize(25, 12)
        lbl.setStyleSheet("background-color: transparent")
        lyt.addWidget(lbl)

        wid = PyDMLabel()
        wid.setMinimumWidth(64)
        lyt.addWidget(wid)
        setattr(self, f"{min_max.lower()}_lbl", wid)

        wid = PyDMByteIndicator()
        wid.setFixedSize(14, 14)
        wid.showLabels = False
        # wid.offColor = Qt.red
        lyt.addWidget(wid)
        setattr(self, f"{min_max.lower()}_bit", wid)

        self.main_lyt.addLayout(lyt)

    def order_thresholds(self, value, **kw):
        """Set Min/Max channels based on the device's slope (value)."""
        min_ch, max_ch = ("L", "H") if value >= 0 else ("H", "L")

        self.min_lbl.channel = f"ca://{self.dev}_{min_ch}_RBV"
        self.min_bit.channel = f"ca://{self.dev}_{min_ch}_EN_RBV"
        self.max_lbl.channel = f"ca://{self.dev}_{max_ch}_RBV"
        self.max_bit.channel = f"ca://{self.dev}_{max_ch}_EN_RBV"


class ConfWriteBPM(QWidget):
    def __init__(self, parent, devs):
        super(ConfWriteBPM, self).__init__(parent=parent)
        self.devs = {}
        self.slope_pvs = []
        self.main_lyt = QVBoxLayout()
        self.setLayout(self.main_lyt)

        self.make_row("Min")
        self.make_row("Max")

        for dev in devs:
            slope_pv = f"{dev.rsplit('_', 1)[0]}_SS_RBV"
            self.devs[slope_pv] = (f"{dev}_L", f"{dev}_H")
            self.slope_pvs.append(PV(slope_pv,
                                     callback=partial(self.order_thresholds, dev=dev),
                                     auto_monitor=DBE_VALUE))

    def make_row(self, min_max: str):
        """Makes the Min/Max row of the Write-only widget. Establishes
        slot connections between the row's widgets."""
        lyt = QHBoxLayout()

        lbl = QLabel(min_max)
        lbl.setFixedSize(25, 12)
        lbl.setStyleSheet("background-color: transparent")
        lyt.addWidget(lbl)

        edt = PyDMMultiLineEdit()
        edt.alarmSensitiveContent = True
        edt.returnPressed.connect(self.edt_returned)
        lyt.addWidget(edt)
        setattr(self, f"{min_max.lower()}_edt", edt)

        chk = PyDMMultiCheckbox()
        chk.clicked.connect(self.chk_clicked)
        lyt.addWidget(chk)
        setattr(self, f"{min_max.lower()}_chk", chk)

        self.main_lyt.addLayout(lyt)

    def order_thresholds(self, pvname, value, dev, **kw):
        """Set Min/Max channels based on the device's slope (value)."""
        min_ch, max_ch = ("L", "H") if value >= 0 else ("H", "L")

        self.devs[pvname] = (f"{dev}_{min_ch}", f"{dev}_{max_ch}")

        vals = self.devs.values()
        self.min_edt.channel = ", ".join([ch[0] for ch in vals])
        self.min_chk.channel = ", ".join([f"{ch[0]}_EN" for ch in vals])
        self.max_edt.channel = ", ".join([ch[1] for ch in vals])
        self.max_chk.channel = ", ".join([f"{ch[1]}_EN" for ch in vals])

    @Slot()
    def edt_returned(self):
        """Slot for the PyDMMultiLineEdit. Checks that values match and
        requests user confirmation if they do not."""
        sndr = self.sender()
        txt = sndr.text()

        vals = caget_many([f"{d[:-5]}_RBV" for d in sndr.channel.split(", ")],
                          connection_timeout=(len(self.devs) * .1))
        equiv = True
        first = vals[0]

        for v in vals:
            if v != first:
                equiv = False
                break

        if not equiv:
            ret = QMessageBox.warning(self, "Differing Threshold Values",
                                      "Threshold values are different across multiple devices."
                                      "\n\nContinue writing to all devices?",
                                      QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.No:
                return
        sndr.setText(txt)
        sndr.send_value()

    @Slot(bool)
    def chk_clicked(self, chk):
        """Slot for the PyDMMultiCheckboxes. If enabling the thresholds,
        confirm with the user first."""
        sndr = self.sender()
        if chk:
            ret = QMessageBox.warning(self, "Confirm Enabling Threshold",
                                      f"Enabling Thresholds:\n{sndr.channel.replace('_EN', '')}"
                                      "\n\nContinue to enable thresholds?",
                                      QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.No:
                sndr.setChecked(False)
                return

        sndr.send_value(chk)
