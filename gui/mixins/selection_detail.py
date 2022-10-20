from json import dumps
from functools import partial
from qtpy.QtCore import (Qt, Slot, QItemSelection)
from qtpy.QtWidgets import (QHeaderView, QTableWidget, QTableWidgetItem)
from epics import PV
from epics.dbr import DBE_VALUE
from pydm.widgets.related_display_button import PyDMRelatedDisplayButton


class SelectionDetailsMixin:
    dest_order = [-1, -1, 3, 2, 4, 5, 1, 6]

    def selection_init(self):
        hdr = self.ui.dtls_truth_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)

        hdr = self.ui.dtls_pv_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)

        self.splitter_state = [1, 300]
        self.ui.logic_spltr.setSizes([1, 0])
        self.ui.logic_spltr.setCollapsible(0, False)
        self.ui.logic_spltr.setStretchFactor(0, 1)

        self.state_pv = None

    def selection_connections(self):
        """Set up slot connections for the Selection Details section."""
        # Establish connections for the SelectionDetails widget
        self.ui.logic_tbl.selectionModel().selectionChanged.connect(
            self.selected)
        self.ui.dtls_close_btn.clicked.connect(self.details_closed)
        self.ui.logic_spltr.splitterMoved.connect(self.save_split_state)

        # Set maximum table size if it contains 1 row
        self.ui.dtls_truth_tbl.itemChanged.connect(
            partial(self.table_max_size, self.ui.dtls_truth_tbl))
        self.ui.dtls_pv_tbl.itemChanged.connect(
            partial(self.table_max_size, self.ui.dtls_pv_tbl))

    def set_fault_details(self, fault, ign_cond):
        """Get the fault's device and inputs. Set necessary labels in
        the Selection Details section."""
        dev = self.model.fault_to_dev(fault.fault)
        inp = self.model.fault_to_inp(fault.fault)

        # Set information at the top of the section
        self.ui.dtls_byp_btn.macros = dumps({"DEVICE_BYP": fault.name})
        self.ui.dtls_name_lbl.setText(fault.description)

        self.ui.dtls_ign_lbl.setText(ign_cond if ign_cond else "--")

        # Set cells in the Truth Table and PV Table
        self.pop_truth_table(fault)
        self.pop_pv_table(fault, dev, inp)

    def clear_table(self, table, row_count, col_count):
        """Clear the contents of the Truth Table or PV Table."""
        table.clearContents()
        table.setRowCount(row_count)
        for i in range(row_count):
            for j in range(col_count):
                table.setItem(i, j, CellItem("--"))

    def pop_truth_table(self, fault):
        """Populate the truth_table. Value is a binary number
        represented as F's and T's. Allowed classes fill destinations."""
        # Values need to be shifted for specific analog devices
        if "X Orbit" in fault.description:
            shift_val = 8
        elif "Y Orbit" in fault.description:
            shift_val = 16
        else:
            shift_val = 0

        # Determine the length of the longest value to zfill others
        shifted_val = fault.fault.states[-1].device_state.value >> shift_val
        max_len = len(format(shifted_val, 'b'))

        self.clear_table(self.ui.dtls_truth_tbl, len(fault.fault.states), 8)
        for i, state in enumerate(fault.fault.states):
            item0 = CellItem(state.device_state.description)

            shifted_val = state.device_state.value >> shift_val
            value_str = format(shifted_val, 'b').zfill(max_len)
            value_str = value_str.replace('0', 'F').replace('1', 'T')
            item1 = CellItem(value_str)

            self.ui.dtls_truth_tbl.setItem(i, 0, item0)
            self.ui.dtls_truth_tbl.setItem(i, 1, item1)

            for cl in state.allowed_classes:
                if cl.beam_class.name == "Full":
                    continue

                col = self.dest_order.index(cl.beam_destination.id)
                item = CellItem(cl.beam_class.name)
                self.ui.dtls_truth_tbl.setItem(i, col, item)

    def pop_pv_table(self, fault, dev, inp):
        """Display all PVs used by digital devices or all inputs of
        analog devices. Rightmost column is a button to open the link
        node associated with the faulted device."""
        analog = dev.is_analog()
        dev_macros = self.node_macros(dev)

        if analog:
            row_count = len(fault.fault.states)
        else:
            row_count = len(inp)

        self.clear_table(self.ui.dtls_pv_tbl, row_count, 4)
        for i in range(row_count):
            if analog:
                pv = f"{inp[0]}_T{i}_SCMPSC"
            else:
                pv = f"{inp[i]}_SCMPSC"

            item0 = CellItem(str(i))
            item1 = CellItem(pv + "C")
            item2 = CellItem(pv)
            self.ui.dtls_pv_tbl.setItem(i, 0, item0)
            self.ui.dtls_pv_tbl.setItem(i, 1, item1)
            self.ui.dtls_pv_tbl.setItem(i, 2, item2)

            ln = dev.card.link_node.lcls1_id
            card = dev.card.number
            if card == 1:
                card = "RTN"
            if analog:
                ch = dev.channel.number
            else:
                ch = dev.inputs[i].channel.number
            btn_txt = f"LN {ln}, Card{card}, Ch {ch}..."

            node_btn = NodeButton(btn_txt, dumps(dev_macros))
            self.ui.dtls_pv_tbl.setCellWidget(i, 3, node_btn)

    def node_macros(self, dev):
        """Populate the macros dict used by the PV table."""
        ret_macros = {}
        ret_macros['ID'] = dev.card.link_node.lcls1_id
        ret_macros['LN'] = dev.card.link_node.lcls1_id
        ret_macros['AREA'] = dev.area.lower()
        ret_macros['AREAU'] = dev.area

    @Slot()
    def save_split_state(self):
        """Saves the splitter size if both sections are not collapsed."""
        sizes = self.ui.logic_spltr.sizes()
        if sizes[-1]:
            self.splitter_state = sizes

    @Slot(QItemSelection, QItemSelection)
    def selected(self, current, previous):
        """Slot called when a row is selected. This will change the
        SelectionDetails widget and open it if it's hidden."""
        indices = current.indexes()
        if not indices:
            indices = previous.indexes()
        row_ind = self.logic_model.mapToSource(indices[0])
        fault = self.faults[row_ind.row()]
        ign_cond = self.ftr_tbl_model.index(row_ind.row(), 8).data()
        self.set_fault_details(fault, ign_cond)
        if not self.ui.logic_spltr.sizes()[1]:
            self.ui.logic_spltr.setSizes(self.splitter_state)

        if self.state_pv:
            self.state_pv.disconnect()
        row = indices[0].row()
        self.state_pv = PV(f"{fault.name}_TEST",
                           callback=partial(self.state_change, row),
                           auto_monitor=DBE_VALUE)
        if not self.state_pv.connected:
            self.ui.dtls_state_lbl.setText("<Fault PVs Not Connected>")

    @Slot()
    def details_closed(self):
        """Slot to close the SelectionDetails widget."""
        self.ui.logic_tbl.clearSelection()
        self.ui.logic_spltr.setSizes([1, 0])

    # State change Callback
    def state_change(self, row, **kw):
        ind = self.logic_model.index(row, 1)
        text = ind.data()
        self.ui.dtls_state_lbl.setText(text)

    @Slot(QTableWidget)
    def table_max_size(self, table):
        """Set the Maximum Height when there is only one row."""
        if table.rowCount() == 1:
            table.setMaximumHeight(49)
        else:
            table.setMaximumHeight(16777215)


class CellItem(QTableWidgetItem):
    """Personalized QTableWidgetItem that sets preferred settings."""
    def __init__(self, text: str, *args, **kwargs):
        super(CellItem, self).__init__(text, *args, **kwargs)
        self.setTextAlignment(Qt.AlignCenter)
        self.setBackground(Qt.white)


class NodeButton(PyDMRelatedDisplayButton):
    """Personalized PyDMRelatedDisplayButton to set preferred settings."""
    def __init__(self, text: str, macros: str):
        super(NodeButton, self).__init__(filename="$PYDM/mps/mps_cn_inputs.ui")
        self.setText(text)
        self.showIcon = False
        self.openInNewWindow = True
        self.macros = macros
