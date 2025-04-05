from tkinter import Tk, filedialog, messagebox, Text, Scrollbar, END, Frame
from tkinter import StringVar
from tkinter import ttk
import socket, os, subprocess
from cryptography.fernet import Fernet

# Config
ports = [8081, 8082, 8083]
host = "127.0.0.1"
file_parts = ["client_part1.dat", "client_part2.dat", "client_part3.dat"]
output_file = "reconstructed_sample.txt"
selected_file = ""
fernet = None

# Logging
def log(message):
    txt_log.insert(END, f"{message}\n")
    txt_log.see(END)

# Generate key
def generate_key():
    global fernet
    key = Fernet.generate_key()
    with open("encryption.key", "wb") as kf:
        kf.write(key)
    fernet = Fernet(key)
    lbl_key.set("🔑 Key saved: encryption.key")
    log("🔐 Encryption key generated and saved.")

# File selection
def select_file():
    global selected_file
    selected_file = filedialog.askopenfilename()
    if selected_file:
        lbl_file.set(f"📁 {os.path.basename(selected_file)}")
        log(f"📁 Selected file: {selected_file}")

# Split and encrypt
def split_and_encrypt_file():
    if not selected_file:
        messagebox.showwarning("No file", "Please select a file.")
        return
    with open(selected_file, "rb") as f:
        data = f.read()
    part_size = len(data) // 3
    parts = [data[:part_size], data[part_size:part_size*2], data[part_size*2:]]
    for i in range(3):
        encrypted = fernet.encrypt(parts[i])
        with open(file_parts[i], "wb") as pf:
            pf.write(encrypted)
    log("🔐 File split and encrypted.")

# Send to server
def send_file_to_server(port, filename):
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
        log(f"✅ Sent {filename} to port {port}")
    except Exception as e:
        log(f"❌ Sending failed: {e}")

# Retrieve from server
def retrieve_file_from_server(port, filename):
    try:
        s = socket.socket()
        s.connect((host, port))
        s.send(b"GET")
        s.send(len(filename.encode()).to_bytes(4, 'big'))
        s.send(filename.encode())
        size = int.from_bytes(s.recv(4), 'big')
        if size == 0:
            log(f"⚠️ {filename} not found at port {port}")
            return None
        data = b''
        while len(data) < size:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        log(f"📥 Retrieved {filename} from port {port}")
        return data
    except Exception as e:
        log(f"❌ Retrieval failed: {e}")
        return None

# Merge and decrypt
def merge_and_decrypt_files():
    merged = b''
    for filename in file_parts:
        port = ports[file_parts.index(filename)]
        encrypted_data = retrieve_file_from_server(port, filename)
        if encrypted_data:
            try:
                decrypted = fernet.decrypt(encrypted_data)
                merged += decrypted
            except Exception as e:
                log(f"❌ Decryption error for {filename}: {e}")
                return
        else:
            return
    with open(output_file, "wb") as out:
        out.write(merged)
    log(f"✅ File reconstructed as {output_file}")
    messagebox.showinfo("Success", f"Reconstructed: {output_file}")

# Process all
def send_and_reconstruct():
    if not selected_file:
        messagebox.showwarning("No file", "Please select a file.")
        return
    log("🔁 Starting process...")
    generate_key()
    split_and_encrypt_file()
    for i in range(3):
        send_file_to_server(ports[i], file_parts[i])
    merge_and_decrypt_files()

# Reset
def reset_ui():
    global selected_file
    selected_file = ""
    lbl_file.set("No file selected.")
    lbl_key.set("")
    txt_log.delete(1.0, END)
    log("🔄 Reset complete.")

# Open output
def open_output_file():
    if os.path.exists(output_file):
        subprocess.Popen(["notepad", output_file])
    else:
        messagebox.showwarning("Missing", "No reconstructed file found.")

# Setup UI
root = Tk()
root.title("🔐 Secure File Splitter & Rebuilder")
root.geometry("600x600")
root.configure(bg="#f0f4f7")

# Style
style = ttk.Style(root)
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 11))
style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))

# Variables
lbl_file = StringVar(value="No file selected.")
lbl_key = StringVar()

# Frames
frame_top = Frame(root, bg="#f0f4f7")
frame_top.pack(pady=10)

ttk.Label(frame_top, text="📦 Secure File Splitter & Rebuilder", style="Header.TLabel").pack()

ttk.Label(root, textvariable=lbl_file, foreground="blue").pack(pady=5)
ttk.Label(root, textvariable=lbl_key, foreground="green").pack()

ttk.Button(root, text="📁 Select File", command=select_file).pack(pady=5)
ttk.Button(root, text="🔄 Encrypt & Reconstruct", command=send_and_reconstruct).pack(pady=5)
ttk.Button(root, text="📂 Open Reconstructed File", command=open_output_file).pack(pady=5)

frame_bottom = Frame(root, bg="#f0f4f7")
frame_bottom.pack(pady=10)
ttk.Button(frame_bottom, text="🔁 Reset", command=reset_ui).pack(side="left", padx=10)
ttk.Button(frame_bottom, text="❌ Exit", command=root.quit).pack(side="left", padx=10)

ttk.Label(root, text="📝 Logs:").pack()

# Log window
scrollbar = Scrollbar(root)
txt_log = Text(root, height=15, width=70, wrap="word", yscrollcommand=scrollbar.set, bg="#ffffff", relief="solid", font=("Consolas", 10))
txt_log.pack(padx=10, pady=5)
scrollbar.config(command=txt_log.yview)
scrollbar.pack(side="right", fill="y")

root.mainloop()
