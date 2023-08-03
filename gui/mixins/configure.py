from qtpy.QtCore import (Qt, Slot, QModelIndex, QSortFilterProxyModel)
from qtpy.QtWidgets import QHeaderView
from mps_database.models import Device
from models_pkg.configure_model import ConfigureTableModel


class ConfigureMixin:
    def configure_init(self):
        """Initializer for everything in Configure tab: ListViews and
        PyDMEmbeddedDisplay."""
        self.ui.configure_spltr.setSizes([50, 50])
        devs = self.model.config.session.query(Device).all()

        # Set model, filter, and header for the All Devices table
        self.all_devs_model = ConfigureTableModel(self, devs)
        self.all_devs_filter = QSortFilterProxyModel(self)
        self.all_devs_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.all_devs_filter.setSourceModel(self.all_devs_model)
        self.ui.all_devs_tbl.setModel(self.all_devs_filter)
        self.ui.all_devs_tbl.sortByColumn(1, Qt.AscendingOrder)
        hdr = self.ui.all_devs_tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # Set model, filter, and header for the Selected Devices table
        self.sel_devs_model = ConfigureTableModel(self, [], save_type=True)
        self.sel_devs_filter = QSortFilterProxyModel(self)
        self.sel_devs_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.sel_devs_filter.setSourceModel(self.sel_devs_model)
        self.ui.sel_devs_tbl.setModel(self.sel_devs_filter)
        self.ui.sel_devs_tbl.sortByColumn(1, Qt.AscendingOrder)
        hdr = self.ui.sel_devs_tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.curr_config = None

    def configure_connections(self):
        """Establish PV and slot connections for the devices model and
        configure tab."""
        # All Devices table and LineEdit
        self.ui.all_devs_edt.textChanged.connect(self.all_devs_filter.setFilterFixedString)
        self.ui.all_devs_tbl.clicked.connect(self.dev_selected)

        # Selected Devices table and LineEdit
        self.ui.sel_devs_edt.textChanged.connect(self.sel_devs_filter.setFilterFixedString)
        self.ui.sel_clear_btn.clicked.connect(self.sel_devs_model.clear_data)
        self.ui.sel_devs_tbl.clicked.connect(self.dev_deselect)
        # self.sel_devs_model.table_changed.connect(self.reload_embed)
        self.sel_devs_model.type_changed.connect(self.reload_embed)
        self.sel_devs_model.datum_added.connect(self.add_device)
        self.sel_devs_model.datum_removed.connect(self.remove_device)

    @Slot(QModelIndex)
    def dev_selected(self, index: QModelIndex):
        """When a device is clicked in all_devs_tbl, add it to the
        sel_devs_tbl."""
        if not index.isValid():
            return

        dev_id = self.all_devs_filter.mapToSource(index).row()
        dev = self.all_devs_model.get_device(dev_id)
        self.sel_devs_model.add_datum(dev)

    @Slot(QModelIndex)
    def dev_deselect(self, index: QModelIndex):
        """When a device is clicked in sel_devs_tbl, remove it."""
        if not index.isValid():
            return

        dev_id = self.sel_devs_filter.mapToSource(index).row()
        self.sel_devs_model.remove_datum(dev_id)

    @Slot(type)
    def reload_embed(self, dev_type):
        """Reload the embedded display when the Selected Devices table
        content changes. Load the associated Configure Display."""
        devices = self.sel_devs_model.get_devices()
        if isinstance(self.curr_config, dev_type):
            self.curr_config.set_devices(devices)
        else:
            self.curr_config = dev_type(devices=devices, model=self.model)
            self.ui.configure_spltr.replaceWidget(1, self.curr_config)

    @Slot(Device)
    def add_device(self, device):
        self.curr_config.add_device(device)

    @Slot(Device)
    def remove_device(self, device):
        self.curr_config.remove_device(device)
