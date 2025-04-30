from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
import socket, os, subprocess, time, threading, json, random, sys
from cryptography.fernet import Fernet

# Ports and file setup
ports = [(8081, 8082), (8082, 8083), (8083, 8081)]
host = "127.0.0.1"
file_parts = ["client_part1.dat", "client_part2.dat", "client_part3.dat"]
output_file = "reconstructed_sample.txt"
metadata_file = "file_metadata.json"
transfer_log_file = "transfer_log.json"
selected_file = ""
fernet = None
stop_animation = False
load_balancer_counter = 0

class Worker(QObject):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    animation_signal = pyqtSignal(bool)
    key_signal = pyqtSignal(str)
    file_signal = pyqtSignal(str)
    done_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.stop_animation = False

    def process(self):
        self.stop_animation = False
        self.animation_signal.emit(False)
        self.progress_signal.emit(0)
        
        self.generate_key()
        self.progress_signal.emit(15)
        time.sleep(0.5)

        self.split_and_encrypt_file()
        self.progress_signal.emit(30)
        time.sleep(0.5)

        for i in range(3):
            main_port, replica_port = ports[i]
            self.send_file_to_server(main_port, file_parts[i])
            self.send_file_to_server(replica_port, file_parts[i])
            self.progress_signal.emit(50 + (i+1)*10)
            time.sleep(0.5)

        self.merge_and_decrypt_files()
        self.progress_signal.emit(100)
        self.stop_animation = True
        self.animation_signal.emit(True)
        self.status_signal.emit("✅ Done!")
        self.log_signal.emit("🎉 All operations completed successfully.")
        self.done_signal.emit()

    def generate_key(self):
        global fernet
        key = Fernet.generate_key()
        with open("encryption.key", "wb") as kf:
            kf.write(key)
        fernet = Fernet(key)
        self.key_signal.emit("✨🔑 Key saved: encryption.key")
        self.log_signal.emit("🔐 Encryption key generated and saved.")

    def split_and_encrypt_file(self):
        if not selected_file:
            self.log_signal.emit("⚠️ No file selected")
            return
            
        with open(selected_file, "rb") as f:
            data = f.read()
        part_size = len(data) // 3
        parts = [data[:part_size], data[part_size:part_size*2], data[part_size*2:]]
        for i in range(3):
            encrypted = fernet.encrypt(parts[i])
            with open(file_parts[i], "wb") as pf:
                pf.write(encrypted)
            self.log_signal.emit(f"📦 Created part {i+1}")
        self.log_signal.emit("🔐 File split and encrypted.")

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
            self.log_signal.emit(f"✅ Sent {filename} to port {port}")

            self.store_metadata(filename, "client", port)
            self.store_transfer_log(filename, port)

        except Exception as e:
            self.log_signal.emit(f"❌ Sending to port {port} failed: {e}")

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
                self.log_signal.emit(f"⚠️ {filename} not found at port {port}")
                return None
            data = b''
            while len(data) < size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            s.close()
            self.log_signal.emit(f"📥 Retrieved {filename} from port {port}")
            self.store_metadata(filename, port, "client")
            return data
        except Exception as e:
            self.log_signal.emit(f"❌ Retrieval from port {port} failed: {e}")
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
            if not encrypted_data:
                self.log_signal.emit(f"⚠️ Main server failed. Trying replica for {filename}...")
                encrypted_data = self.retrieve_file_from_server(replica_port, filename)
                if not encrypted_data:
                    self.log_signal.emit(f"❌ Both main and replica failed for {filename}")
                    return

            try:
                decrypted = fernet.decrypt(encrypted_data)
                merged += decrypted
            except Exception as e:
                self.log_signal.emit(f"❌ Decryption error for {filename}: {e}")
                return

        with open(output_file, "wb") as out:
            out.write(merged)
        self.log_signal.emit(f"✅ File reconstructed as {output_file}")
        self.done_signal.emit()

    def choose_port(self, index):
        global load_balancer_counter
        main_port, replica_port = ports[index]
        chosen = main_port if load_balancer_counter % 2 == 0 else replica_port
        load_balancer_counter += 1
        return chosen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 Secure File Splitter & Rebuilder")
        self.setGeometry(100, 100, 700, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.setup_ui()
        self.worker_thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_status)
        self.worker.log_signal.connect(self.log)
        self.worker.animation_signal.connect(self.set_animation_state)
        self.worker.key_signal.connect(self.update_key_label)
        self.worker.file_signal.connect(self.update_file_label)
        self.worker.done_signal.connect(self.on_operation_complete)
        
        self.worker_thread.start()
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_status)
        self.animation_counter = 0
        self.animation_msg = ""
        
    def setup_ui(self):
        # Header
        self.header = QLabel("📦 DISTRIBUTED SYSTEM")
        self.header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)
        
        # File info labels
        self.file_label = QLabel("No file selected.")
        self.file_label.setStyleSheet("color: blue;")
        self.layout.addWidget(self.file_label, alignment=Qt.AlignCenter)
        
        self.key_label = QLabel()
        self.key_label.setStyleSheet("color: green;")
        self.layout.addWidget(self.key_label, alignment=Qt.AlignCenter)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: darkgreen; font-style: italic;")
        self.layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        
        # Buttons
        self.select_file_btn = QPushButton("📁 Select File")
        self.select_file_btn.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_file_btn)
        
        self.logs_btn = QPushButton("📁 See index of transfers")
        self.logs_btn.clicked.connect(self.logs_ui)
        self.layout.addWidget(self.logs_btn)
        
        self.reconstruct_btn = QPushButton("🔄 Encrypt & Reconstruct")
        self.reconstruct_btn.clicked.connect(self.send_and_reconstruct)
        self.layout.addWidget(self.reconstruct_btn)
        
        self.open_file_btn = QPushButton("📂 Open Reconstructed File")
        self.open_file_btn.clicked.connect(self.open_output_file)
        self.layout.addWidget(self.open_file_btn)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)
        
        # Bottom buttons
        self.bottom_frame = QFrame()
        self.bottom_layout = QHBoxLayout(self.bottom_frame)
        
        self.reset_btn = QPushButton("🔁 Reset")
        self.reset_btn.clicked.connect(self.reset_ui)
        self.bottom_layout.addWidget(self.reset_btn)
        
        self.exit_btn = QPushButton("❌ Exit")
        self.exit_btn.clicked.connect(self.close)
        self.bottom_layout.addWidget(self.exit_btn)
        
        self.layout.addWidget(self.bottom_frame)
        
        # Console
        self.console_label = QLabel("🖥️ Command Console")
        self.console_label.setFont(QFont("Segoe UI", 14))
        self.layout.addWidget(self.console_label)
        
        self.console_input = QTextEdit()
        self.console_input.setMaximumHeight(100)
        self.console_input.setFont(QFont("Courier New", 12))
        self.console_input.keyPressEvent = self.console_key_press_event
        self.layout.addWidget(self.console_input)
        
        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 12))
        self.layout.addWidget(self.log_output)
        
    def console_key_press_event(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers():
            self.handle_console_input()
        else:
            QTextEdit.keyPressEvent(self.console_input, event)
            
    def handle_console_input(self):
        command = self.console_input.toPlainText().strip().lower()
        self.console_input.clear()
        
        if command == "generate_key":
            self.worker.generate_key()
        elif command == "select_file":
            self.select_file()
        elif command == "split_by_nodes":
            self.worker.split_and_encrypt_file()
        elif command == "distribute_file":
            self.send_and_reconstruct()
        elif command == "reconstruct_file":
            self.open_output_file()
        elif command == "reset_ui":
            self.reset_ui()
        elif command == "exit":
            self.close()
        elif command == "help":
            self.log("Commands:\n"
                    "generate_key\nselect_file\nsplit_by_nodes\ndistribute_file\n"
                    "reconstruct_file\nreset_ui\nexit\nhelp")
        else:
            self.log(f"Unknown command: {command}")
    
    def select_file(self):
        global selected_file
        selected_file, _ = QFileDialog.getOpenFileName(self, "Select File")
        if selected_file:
            self.file_label.setText(f"📁 {os.path.basename(selected_file)}")
            self.log(f"📁 Selected file: {selected_file}")
    
    def send_and_reconstruct(self):
        global selected_file
        if not selected_file:
            QMessageBox.warning(self, "No file", "Please select a file.")
            return
            
        self.animation_msg = "🔁 Working"
        self.animation_counter = 0
        self.animation_timer.start(500)
        
        # Start worker process
        QTimer.singleShot(0, self.worker.process)
    
    def animate_status(self):
        self.status_label.setText(self.animation_msg + "." * (self.animation_counter % 4))
        self.animation_counter += 1
    
    def set_animation_state(self, stop):
        if stop:
            self.animation_timer.stop()
    
    def update_progress(self, value):
        self.progress.setValue(value)
    
    def update_status(self, text):
        self.status_label.setText(text)
    
    def update_key_label(self, text):
        self.key_label.setText(text)
    
    def update_file_label(self, text):
        self.file_label.setText(text)
    
    def log(self, message):
        self.log_output.moveCursor(QTextCursor.End)
        self.log_output.insertPlainText(f"{message}\n")
        self.log_output.ensureCursorVisible()
    
    def reset_ui(self):
        global selected_file
        selected_file = ""
        self.file_label.setText("No file selected.")
        self.key_label.clear()
        self.status_label.clear()
        self.log_output.clear()
        self.progress.setValue(0)
        self.animation_timer.stop()
        self.log("🔄 Reset complete.")
    
    def open_output_file(self):
        if os.path.exists(output_file):
            subprocess.Popen(["notepad", output_file])
        else:
            QMessageBox.warning(self, "Missing", "No reconstructed file found.")
    
    def logs_ui(self):
        subprocess.run([sys.executable, "logs_ui.py"])
    
    def on_operation_complete(self):
        QMessageBox.information(self, "Success", f"Reconstructed: {output_file}")
    
    def closeEvent(self, event):
        self.worker_thread.quit()
        self.worker_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())