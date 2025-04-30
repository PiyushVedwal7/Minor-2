import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

class ServerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Server Authentication")
        self.setGeometry(200, 200, 300, 150)

        # Layout
        layout = QVBoxLayout()

        # ID field
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("Enter ID")
        layout.addWidget(self.id_input)

        # Password field
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Start Servers button
        self.start_button = QPushButton("Start Servers", self)
        self.start_button.clicked.connect(self.start_servers)
        layout.addWidget(self.start_button)

        # Set layout
        self.setLayout(layout)

    def start_servers(self):
        user_id = self.id_input.text()
        password = self.password_input.text()

        # Hardcoded ID and Password
        correct_id = "admin"
        correct_password = "1234"

        # Check if entered ID and Password are correct
        if user_id != correct_id or password != correct_password:
            QMessageBox.warning(self, "Authentication Error", "Invalid ID or Password")
            return

        # If correct, start the servers
        self.run_server_in_background(8081)
        self.run_server_in_background(8082)
        self.run_server_in_background(8083)

        QMessageBox.information(self, "Success", "Servers are running on ports 8081, 8082, and 8083!")

    def run_server_in_background(self, port):
        # Run the server script in the background using subprocess
        subprocess.Popen([sys.executable, 's1.py', str(port)])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ServerUI()
    window.show()
    sys.exit(app.exec_())
