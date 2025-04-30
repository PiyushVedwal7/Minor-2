# a_ui.py

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QMainWindow, QListWidget
import os

# --- Data Node Window (Limited Access) ---
class DataNodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Node Window - File Presence Only")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.list_widget = QListWidget()

        # Populate list with files
        self.update_file_list()

        layout.addWidget(QLabel("Files in the System:"))
        layout.addWidget(self.list_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_file_list(self):
        files = os.listdir('.')  # Current Directory
        self.list_widget.clear()
        for file in files:
            self.list_widget.addItem(file)

# --- Admin Window (Your Original Full Control Window) ---
class AdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Window - Full Control")
        self.setGeometry(600, 100, 500, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        label = QLabel("Admin Full Control Window - All functionalities here.")

        # Add your existing buttons and functionalities here
        layout.addWidget(label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # TODO: Integrate your previous a_ui.py UI elements here
        # (Currently placed a placeholder Label. You can paste your original controls.)

# --- Role Selection Window ---
class RoleSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Role")
        self.setGeometry(400, 200, 300, 150)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Select your role:")
        layout.addWidget(self.label)

        self.admin_button = QPushButton("Admin Login")
        self.admin_button.clicked.connect(self.admin_login)
        layout.addWidget(self.admin_button)

        self.data_node_button = QPushButton("Data Node Login")
        self.data_node_button.clicked.connect(self.data_node_login)
        layout.addWidget(self.data_node_button)

        self.setLayout(layout)

    def admin_login(self):
        self.admin_window = AdminWindow()
        self.admin_window.show()

        self.data_node_window = DataNodeWindow()
        self.data_node_window.show()

        # Start background processes (s1.py and s2.py)
        subprocess.Popen([sys.executable, "s1.py"])
        subprocess.Popen([sys.executable, "s2.py"])

        self.close()

    def data_node_login(self):
        self.data_node_window = DataNodeWindow()
        self.data_node_window.show()
        self.close()

# --- Main Code Execution ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    role_window = RoleSelectionWindow()
    role_window.show()
    sys.exit(app.exec_())