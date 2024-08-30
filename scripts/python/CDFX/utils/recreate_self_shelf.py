"""
This script recreates selected nodes in Houdini.
"""

import hou #type: ignore
import sys
from PySide2 import QtWidgets, QtCore #type: ignore
from importlib import reload
import CDFX.utils.recreate_self
reload(CDFX.utils.recreate_self)

from CDFX.utils.recreate_self import recreate_self

def run_recreate_self_shelf(show_dialog=True):
    selected_nodes = hou.selectedNodes()

    if not selected_nodes:
        hou.ui.displayMessage("No nodes selected")
        return

    if show_dialog:
        class Dialog(QtWidgets.QDialog):
            def __init__(self):
                super(Dialog, self).__init__()

                self.initUI()

            def initUI(self):
                self.setWindowTitle('Options')
                self.setGeometry(400, 400, 400, 220)

                self.checkbox1 = QtWidgets.QCheckBox("Destroy Old Node", self)
                self.checkbox1.move(20, 20)
                self.checkbox1.setChecked(False)  # Set default value

                self.checkbox2 = QtWidgets.QCheckBox("Grab Latest Version", self)
                self.checkbox2.move(20, 50)
                self.checkbox2.setChecked(True)  # Set default value

                
                self.checkbox3 = QtWidgets.QCheckBox("Keep Children (nodes with 'keep' in name)", self)
                self.checkbox3.move(20, 80)
                self.checkbox3.setChecked(True)  # Set default value

                self.checkbox4 = QtWidgets.QCheckBox("Use New Nodes' Parameter Defaults", self)
                self.checkbox4.move(20, 110)
                self.checkbox4.setChecked(True)  # Set default value

                self.checkbox5 = QtWidgets.QCheckBox("Print Diagnostics", self)
                self.checkbox5.move(20, 140)
                self.checkbox5.setChecked(False)  # Set default value
                
                btn = QtWidgets.QPushButton('OK', self)
                btn.move(20, 170)
                btn.clicked.connect(self.accept)

                btnCancel = QtWidgets.QPushButton('Cancel', self)
                btnCancel.move(120, 170)
                btnCancel.clicked.connect(self.reject)

                self.show()

            def getCheckboxValues(self):
                return (
                    self.checkbox1.isChecked(),
                    self.checkbox2.isChecked(),
                    self.checkbox3.isChecked(),
                    self.checkbox4.isChecked(),
                    self.checkbox5.isChecked()
                )

        dlg = Dialog()
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            node_destroy_check, grab_latest, keep_children, use_new_parm_defaults, print_diagnostics = dlg.getCheckboxValues()
        else:
            return
    else:
        # Default values if not showing dialog
        node_destroy_check, grab_latest, keep_children, use_new_parm_defaults, print_diagnostics = False, True, True, True, False

    # Recreate the selected nodes
    for node in selected_nodes:
        recreate_self(node, node_destroy_check, grab_latest, keep_children, use_new_parm_defaults, print_diagnostics)

if __name__ == "__main__":
    run_recreate_self_shelf()