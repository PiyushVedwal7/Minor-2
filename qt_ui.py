from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QLineEdit, QFileDialog, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QThread
from cryptography.fernet import Fernet
import sys
import os
import time
import socket
import threading
import subprocess
import json


class SecureFileSplitter(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🔐 Secure File Splitter & Rebuilder")
        self.setGeometry(100, 100, 700, 700)
        self.setStyleSheet("background-color: #f0f4f7;")

        self.selected_file = ""
        self.fernet = None
        self.stop_animation = False
        self.load_balancer_counter = 0

        self.init_ui()

    def init_ui(self):
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Title
        self.title_label = QLabel("📦 DISTRIBUTED SYSTEM")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        self.layout.addWidget(self.title_label)

        # File selection and key label
        self.lbl_file = QLabel("No file selected.")
        self.lbl_key = QLabel("")
        self.lbl_status = QLabel("")
        self.lbl_file.setStyleSheet("color: blue; font-size: 14px;")
        self.lbl_key.setStyleSheet("color: green; font-size: 14px;")
        self.lbl_status.setStyleSheet("color: darkgreen; font-size: 12px; font-style: italic;")
        
        self.layout.addWidget(self.lbl_file)
        self.layout.addWidget(self.lbl_key)
        self.layout.addWidget(self.lbl_status)

        # Buttons
        self.select_file_button = QPushButton("📁 Select File")
        self.select_file_button.clicked.connect(self.select_file)

        self.encrypt_and_reconstruct_button = QPushButton("🔄 Encrypt & Reconstruct")
        self.encrypt_and_reconstruct_button.clicked.connect(self.send_and_reconstruct)

        self.open_output_button = QPushButton("📂 Open Reconstructed File")
        self.open_output_button.clicked.connect(self.open_output_file)

        self.reset_button = QPushButton("🔁 Reset")
        self.reset_button.clicked.connect(self.reset_ui)

        self.exit_button = QPushButton("❌ Exit")
        self.exit_button.clicked.connect(self.close)

        self.layout.addWidget(self.select_file_button)
        self.layout.addWidget(self.encrypt_and_reconstruct_button)
        self.layout.addWidget(self.open_output_button)

        # Progress Bar
        self.progress = QProgressBar()
        self.layout.addWidget(self.progress)

        # Console
        self.console_label = QLabel("🖥️ Command Console")
        self.console_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.layout.addWidget(self.console_label)

        self.console_input = QTextEdit(self)
        self.console_input.setStyleSheet("font-family: Courier New; font-size: 12px;")
        self.console_input.setPlaceholderText("Enter commands here...")
        self.console_input.keyPressEvent = self.handle_key_press_event  # Handle key press event manually
        self.layout.addWidget(self.console_input)

        # Log area
        self.txt_log = QTextEdit(self)
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("font-family: Courier New; font-size: 12px;")
        self.layout.addWidget(self.txt_log)

        # Set up a timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.sparkle_animation)

    def handle_key_press_event(self, event):
        """ Handle the 'Enter' key press event in QTextEdit. """
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.handle_console_input()
        else:
            super(QTextEdit, self).keyPressEvent(event)  # For other key events

    def handle_console_input(self):
        input_text = self.console_input.toPlainText().strip()
        if input_text:
            self.log(f"💬 Console Input: {input_text}")
            self.console_input.clear()

    def sparkle_animation(self):
        # Basic animation for the sparkle effect
        pass  # This can be enhanced with actual graphical sparkle animation if needed

    def log(self, message):
        self.txt_log.append(f"{message}\n")

    def generate_key(self):
        global fernet
        key = Fernet.generate_key()
        with open("encryption.key", "wb") as kf:
            kf.write(key)
        fernet = Fernet(key)
        self.lbl_key.setText(f"✨🔑 Key saved: encryption.key")
        self.log("🔐 Encryption key generated and saved.")

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if file:
            self.selected_file = file
            self.lbl_file.setText(f"📁 {os.path.basename(file)}")
            self.log(f"📁 Selected file: {file}")

    def split_and_encrypt_file(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No file", "Please select a file.")
            return
        with open(self.selected_file, "rb") as f:
            data = f.read()
        part_size = len(data) // 3
        parts = [data[:part_size], data[part_size:part_size*2], data[part_size*2:]]
        for i in range(3):
            encrypted = fernet.encrypt(parts[i])
            with open(file_parts[i], "wb") as pf:
                pf.write(encrypted)
            self.fly_file_part(f"📦 Part {i+1}")
        self.log("🔐 File split and encrypted.")

    def fly_file_part(self, label_text):
        label = QLabel(label_text)
        label.setStyleSheet("background-color: #f0f4f7; font-size: 10px; font-weight: bold;")
        self.layout.addWidget(label)

        def move():
            for i in range(30):
                label.move(20 + i*10, 500 - i*5)
                time.sleep(0.03)
            label.deleteLater()

        threading.Thread(target=move).start()

    def choose_port(self, index):
        global load_balancer_counter
        main_port, replica_port = ports[index]
        chosen = main_port if load_balancer_counter % 2 == 0 else replica_port
        load_balancer_counter += 1
        return chosen

    def send_file_to_server(self, port, filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
            s = socket.socket()
            s.connect((host, port))
            s.send(b"PUT")
            s.send(len(filename.encode()).to_bytes(4, 'big'))
            s.send(filename.encode())
            s.send(len(data).to_bytes(4, 'big'))
            s.sendall(data)
            s.close()
            self.log(f"✅ Sent {filename} to port {port}")
            self.store_metadata(filename, "client", port)
            self.store_transfer_log(filename, port)

        except Exception as e:
            self.log(f"❌ Sending to port {port} failed: {e}")

    def store_transfer_log(self, filename, port):
        transfer_log = []
        if os.path.exists(transfer_log_file):
            with open(transfer_log_file, "r") as f:
                transfer_log = json.load(f)

        transfer_log.append({
            "filename": filename,
            "port": port,
            "timestamp": time.ctime()
        })

        with open(transfer_log_file, "w") as f:
            json.dump(transfer_log, f, indent=4)

    def retrieve_file_from_server(self, port, filename):
        try:
            s = socket.socket()
            s.connect((host, port))
            s.send(b"GET")
            s.send(len(filename.encode()).to_bytes(4, 'big'))
            s.send(filename.encode())
            size = int.from_bytes(s.recv(4), 'big')
            if size == 0:
                self.log(f"⚠️ {filename} not found at port {port}")
                return None
            data = b''
            while len(data) < size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            s.close()
            self.log(f"📥 Retrieved {filename} from port {port}")
            self.store_metadata(filename, port, "client")
            return data
        except Exception as e:
            self.log(f"❌ Retrieval from port {port} failed: {e}")
            return None

    def store_metadata(self, filename, src, dest):
        metadata = {}
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        metadata[filename] = metadata.get(filename, [])
        metadata[filename].append({"from": src, "to": dest, "timestamp": time.ctime()})
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)

    def merge_and_decrypt_files(self):
        merged = b''
        for filename in file_parts:
            index = file_parts.index(filename)
            main_port, replica_port = ports[index]
            port_to_use = self.choose_port(index)
            encrypted_data = self.retrieve_file_from_server(port_to_use, filename)
            if encrypted_data:
                decrypted = fernet.decrypt(encrypted_data)
                merged += decrypted
            else:
                self.log(f"❌ Failed to retrieve {filename}")
                return
        with open(output_file, "wb") as f:
            f.write(merged)
        self.log(f"✅ Reconstructed file saved as {output_file}")

    def open_output_file(self):
        if os.path.exists(output_file):
            subprocess.Popen(["open", output_file])
        else:
            QMessageBox.warning(self, "No file", "Reconstructed file not found.")

    def reset_ui(self):
        self.selected_file = ""
        self.lbl_file.setText("No file selected.")
        self.lbl_key.setText("")
        self.lbl_status.setText("")
        self.txt_log.clear()


    def send_and_reconstruct(self):
        self.generate_key()
        self.split_and_encrypt_file()
        self.merge_and_decrypt_files()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SecureFileSplitter()
    window.show()
    sys.exit(app.exec_())
