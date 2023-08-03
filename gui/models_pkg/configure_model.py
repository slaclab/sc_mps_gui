from typing import List
from qtpy.QtCore import (Qt, Signal, QModelIndex, QAbstractTableModel)
from mps_database.models import Device
from resources.config_widgets import (ConfDef, ConfErr)
from resources.conf_bpm_embed import ConfBPM


class ConfigureTableModel(QAbstractTableModel):
    hdr_lst = ["Device", "Device Type"]

    table_changed = Signal(type)
    type_changed = Signal(type)
    datum_added = Signal(Device)
    datum_removed = Signal(Device)

    def __init__(self, parent, _data: List[Device], save_type=False):
        super(ConfigureTableModel, self).__init__(parent)
        self._data = _data

        self.type_dict = {}
        if save_type:
            for d in self._data:
                self.add_type(d.device_type.name)

    def rowCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of columns in the model."""
        return len(self.hdr_lst)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        """Return the index's text if requested."""
        if role == Qt.DisplayRole and index.column() == 0:
            return self._data[index.row()].description
        elif role == Qt.DisplayRole and index.column() == 1:
            return self._data[index.row()].device_type.name

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal header's text."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.hdr_lst[section]

    def table_type(self):
        """Return the class for the type(s) in the model."""
        if len(self.type_dict) == 0:
            return ConfDef
        elif len(self.type_dict) > 1:
            return ConfErr
        else:
            key = list(self.type_dict.keys())[0]
            if key == "BPMS":
                return ConfBPM
            else:
                return ConfErr

    def add_type(self, dev_type: str):
        """Add the given device type to the type dictionary."""
        self.type_dict.setdefault(dev_type, 0)
        self.type_dict[dev_type] += 1
        self.type_changed.emit(self.table_type())

    def add_datum(self, datum: Device):
        """Add a single device to the model."""
        if datum in self._data:
            return

        ind = len(self._data)
        self.beginInsertRows(QModelIndex(), ind, ind)
        self._data.append(datum)
        self.endInsertRows()

        self.add_type(datum.device_type.name)
        # self.table_changed.emit(self.table_type())
        self.datum_added.emit(datum)

    def remove_type(self, dev_type: str):
        """Remove the given device type from the type dictionary."""
        if dev_type not in self.type_dict:
            return
        self.type_dict[dev_type] -= 1
        if self.type_dict[dev_type] <= 0:
            del self.type_dict[dev_type]
        self.type_changed.emit(self.table_type())

    def remove_datum(self, index: int):
        """Remove a single device from the model."""
        self.beginRemoveRows(QModelIndex(), index, index)
        datum = self._data.pop(index)
        # del self._data[index]
        self.endRemoveRows()

        self.remove_type(datum.device_type.name)
        # self.table_changed.emit(self.table_type())
        self.datum_removed.emit(datum)

    def clear_data(self):
        """Remove all devices and device types from the model."""
        if not self._data:
            return

        ind = len(self._data) - 1
        self.beginRemoveRows(QModelIndex(), 0, ind)
        self._data = []
        self.endRemoveRows()

        self.type_dict.clear()
        # self.table_changed.emit(self.table_type())
        self.type_changed.emit(self.table_type())

    def get_device(self, index: int):
        """Return the requested device."""
        return self._data[index]

    def get_devices(self):
        return self._data
