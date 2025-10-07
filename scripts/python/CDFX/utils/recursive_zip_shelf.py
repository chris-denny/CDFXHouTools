import hou # type: ignore
import os
try:
    from PySide6 import QtWidgets, QtCore # type: ignore
except ImportError:
    from PySide2 import QtWidgets, QtCore # type: ignore
from CDFX.utils.recursive_zip import run_recursive_zipper

def show_recursive_zip_ui():
    class RecursiveZipUI(QtWidgets.QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Recursive Zip Utility")

            self.layout = QtWidgets.QVBoxLayout()

            self.directory_label = QtWidgets.QLabel("Root Directory:")
            self.directory_input = QtWidgets.QLineEdit()
            self.directory_input.setText("$HIP")
            self.directory_button = QtWidgets.QPushButton("Browse...")
            self.directory_button.clicked.connect(self.select_directory)
            self.layout.addWidget(self.directory_label)
            self.layout.addWidget(self.directory_input)
            self.layout.addWidget(self.directory_button)

            self.folder_label = QtWidgets.QLabel("Backups Folder Name:")
            self.folder_input = QtWidgets.QLineEdit()
            self.folder_input.setText("backup")
            self.layout.addWidget(self.folder_label)
            self.layout.addWidget(self.folder_input)

            self.unattended_checkbox = QtWidgets.QCheckBox("Run Unattended !BE CAREFUL!")
            self.unattended_checkbox.setChecked(False)
            self.layout.addWidget(self.unattended_checkbox)

            self.zip_checkbox = QtWidgets.QCheckBox("Zip")
            self.zip_checkbox.setEnabled(False)
            self.layout.addWidget(self.zip_checkbox)

            self.delete_checkbox = QtWidgets.QCheckBox("Delete")
            self.delete_checkbox.setEnabled(False)
            self.layout.addWidget(self.delete_checkbox)

            # Connect signals
            self.unattended_checkbox.stateChanged.connect(self.toggle_unattended)
            self.zip_checkbox.stateChanged.connect(self.toggle_delete_checkbox)

            self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            self.layout.addWidget(self.buttons)

            self.setLayout(self.layout)

        def toggle_delete_checkbox(self, state):
            self.delete_checkbox.setEnabled(state == QtCore.Qt.Checked)
            self.delete_checkbox.setChecked(False)

        def toggle_unattended(self, state):
            unattended = state == QtCore.Qt.Checked
            if not unattended:
                self.zip_checkbox.setEnabled(False)
                self.zip_checkbox.setChecked(False)
                self.delete_checkbox.setChecked(False)
            else:
                self.zip_checkbox.setEnabled(True)
                self.delete_checkbox.setEnabled(unattended and self.zip_checkbox.isChecked())

        def print_and_confirm_files(self, action, backups_dir, files):
            total_size_mb = self.get_size_mb(sum(size for _, size in files) * 1_000)
            backups_dir = backups_dir.replace("\\", "/")
            message = f"Files to {action} in {backups_dir}:\n"
            
            if len(files) > 10:
                for file, size in files[:5]:
                    message += f"{file} ({size} kB)\n"
                message += f"... {len(files) - 10} more files ...\n"
                for file, size in files[-5:]:
                    message += f"{file} ({size} kB)\n"
            else:
                for file, size in files:
                    message += f"{file} ({size} kB)\n"
            
            message += f"Folder: {backups_dir}\n    Num Files: {len(files)}\n    Total size: {total_size_mb} MB\n"
            message += f"Do you want to {action} these files?"
            
            reply = QtWidgets.QMessageBox.question(self, f"Confirm {action.capitalize()}", message,
                                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            return reply == QtWidgets.QMessageBox.Yes

        def get_size_mb(self, size_bytes):
            return round(size_bytes / 1_000_000, 2)

        def select_directory(self):
            directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory:
                self.directory_input.setText(directory)

    dialog = RecursiveZipUI()
    if dialog.exec_():
        directory = hou.expandString(dialog.directory_input.text().replace("\\", "/"))
        directory = os.path.normpath(directory)
        folder = hou.expandString(dialog.folder_input.text())
        unattended = dialog.unattended_checkbox.isChecked()
        zip_files = unattended and dialog.zip_checkbox.isChecked()
        delete_files = unattended and dialog.delete_checkbox.isChecked()
        print(f"Directory: '{directory}', Folder Search: '{folder}'\nRun Unattended: {unattended}, Force Zip: {zip_files}, Force Delete: {delete_files}")
        
        # Show processing message
        process_msg = QtWidgets.QMessageBox()
        process_msg.setWindowTitle("Working")
        process_msg.setText("Processing files...")
        process_msg.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        process_msg.setWindowModality(QtCore.Qt.WindowModal)
        process_msg.show()
        
        try:
            run_recursive_zipper(
                directory=directory,
                folder=folder,
                zip=zip_files,
                delete=delete_files,
                unattended=unattended,
                parallel=4,
                compression=2,
                print_and_confirm_callback=dialog.print_and_confirm_files
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(None, "Error", str(e))
        finally:
            process_msg.close()  # Ensure the message box is closed