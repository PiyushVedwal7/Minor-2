from tkinter import Tk, filedialog, messagebox, Text, Scrollbar, END, Frame
from tkinter import StringVar
from tkinter import ttk
import socket, os, subprocess
from cryptography.fernet import Fernet

# Each tuple is (main_port, replica_port)
ports = [(8081, 8082), (8082, 8083), (8083, 8081)]
host = "127.0.0.1"
file_parts = ["client_part1.dat", "client_part2.dat", "client_part3.dat"]
output_file = "reconstructed_sample.txt"
selected_file = ""
fernet = None

def log(message):
    txt_log.insert(END, f"{message}\n")
    txt_log.see(END)

def generate_key():
    global fernet
    key = Fernet.generate_key()
    with open("encryption.key", "wb") as kf:
        kf.write(key)
    fernet = Fernet(key)
    lbl_key.set("🔑 Key saved: encryption.key")
    log("🔐 Encryption key generated and saved.")

def select_file():
    global selected_file
    selected_file = filedialog.askopenfilename()
    if selected_file:
        lbl_file.set(f"📁 {os.path.basename(selected_file)}")
        log(f"📁 Selected file: {selected_file}")

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
        log(f"❌ Sending to port {port} failed: {e}")

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
        log(f"❌ Retrieval from port {port} failed: {e}")
        return None

def merge_and_decrypt_files():
    merged = b''
    for filename in file_parts:
        index = file_parts.index(filename)
        main_port, replica_port = ports[index]

        encrypted_data = retrieve_file_from_server(main_port, filename)
        if not encrypted_data:
            log(f"⚠️ Main server failed. Trying replica for {filename}...")
            encrypted_data = retrieve_file_from_server(replica_port, filename)
            if not encrypted_data:
                log(f"❌ Both main and replica failed for {filename}")
                return

        try:
            decrypted = fernet.decrypt(encrypted_data)
            merged += decrypted
        except Exception as e:
            log(f"❌ Decryption error for {filename}: {e}")
            return

    with open(output_file, "wb") as out:
        out.write(merged)
    log(f"✅ File reconstructed as {output_file}")
    messagebox.showinfo("Success", f"Reconstructed: {output_file}")

def send_and_reconstruct():
    if not selected_file:
        messagebox.showwarning("No file", "Please select a file.")
        return
    log("🔁 Starting process...")
    generate_key()
    split_and_encrypt_file()
    for i in range(3):
        main_port, replica_port = ports[i]
        send_file_to_server(main_port, file_parts[i])
        send_file_to_server(replica_port, file_parts[i])
    merge_and_decrypt_files()

def reset_ui():
    global selected_file
    selected_file = ""
    lbl_file.set("No file selected.")
    lbl_key.set("")
    txt_log.delete(1.0, END)
    log("🔄 Reset complete.")

def open_output_file():
    if os.path.exists(output_file):
        subprocess.Popen(["notepad", output_file])
    else:
        messagebox.showwarning("Missing", "No reconstructed file found.")

# GUI
root = Tk()
root.title("🔐 Secure File Splitter & Rebuilder")
root.geometry("600x600")
root.configure(bg="#f0f4f7")

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 11))
style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))

lbl_file = StringVar(value="No file selected.")
lbl_key = StringVar()

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

scrollbar = Scrollbar(root)
txt_log = Text(root, height=15, width=70, wrap="word", yscrollcommand=scrollbar.set, bg="#ffffff", relief="solid", font=("Consolas", 10))
txt_log.pack(padx=10, pady=5)
scrollbar.config(command=txt_log.yview)
scrollbar.pack(side="right", fill="y")

root.mainloop()
