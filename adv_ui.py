from tkinter import Tk, filedialog, messagebox, Text, Scrollbar, END, Frame, Canvas, Label
from tkinter import StringVar
from tkinter import ttk
import socket, os, subprocess, time, threading, json
from cryptography.fernet import Fernet
import random

# Ports and file setup
ports = [(8081, 8082), (8082, 8083), (8083, 8081)]
host = "127.0.0.1"
file_parts = ["client_part1.dat", "client_part2.dat", "client_part3.dat"]
output_file = "reconstructed_sample.txt"
metadata_file = "file_metadata.json"
selected_file = ""
fernet = None
stop_animation = False
load_balancer_counter = 0
MAX_RETRIES = 3  # Max retries for sending/receiving files

# Function to get disk space information
def get_disk_space(path="/"):
    stat = os.statvfs(path)
    total = stat.f_frsize * stat.f_blocks
    available = stat.f_frsize * stat.f_bavail
    used = total - available
    return used, available

def log(message):
    txt_log.insert(END, f"{message}\n")
    txt_log.see(END)

def generate_key():
    global fernet
    key = Fernet.generate_key()
    with open("encryption.key", "wb") as kf:
        kf.write(key)
    fernet = Fernet(key)
    lbl_key.set("✨🔑 Key saved: encryption.key")
    sparkle_animation()
    log("🔐 Encryption key generated and saved.")

def select_file():
    global selected_file
    selected_file = filedialog.askopenfilename()
    if selected_file:
        lbl_file.set(f"📁 {os.path.basename(selected_file)}")
        log(f"📁 Selected file: {selected_file}")

def sparkle_animation():
    for _ in range(10):
        x = random.randint(100, 500)
        y = random.randint(50, 300)
        spark = canvas.create_text(x, y, text="✨", font=("Segoe UI", 16))
        root.after(300, lambda s=spark: canvas.delete(s))

def split_and_encrypt_file():
    if not selected_file:
        messagebox.showwarning("No file", "Please select a file.")
        return
    try:
        with open(selected_file, "rb") as f:
            data = f.read()
        part_size = len(data) // 3
        parts = [data[:part_size], data[part_size:part_size*2], data[part_size*2:]]
        for i in range(3):
            encrypted = fernet.encrypt(parts[i])
            with open(file_parts[i], "wb") as pf:
                pf.write(encrypted)
            fly_file_part(f"📦 Part {i+1}")
        log("🔐 File split and encrypted.")
    except Exception as e:
        log(f"❌ Error during file splitting: {e}")

def fly_file_part(label_text):
    label = Label(canvas, text=label_text, bg="#f0f4f7", font=("Segoe UI", 10, "bold"))
    label.grid(row=500, column=0, padx=10, pady=5)  # Use grid instead of place
    def move():
        for i in range(30):
            label.grid_configure(row=500 - i*5, column=0)  # Use grid_configure
            time.sleep(0.03)
        label.grid_forget()
    threading.Thread(target=move).start()

def choose_port(index):
    global load_balancer_counter
    main_port, replica_port = ports[index]
    chosen = main_port if load_balancer_counter % 2 == 0 else replica_port
    load_balancer_counter += 1
    return chosen

def send_file_to_server(port, filename):
    retries = 0
    while retries < MAX_RETRIES:
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
            store_metadata(filename, "client", port)
            update_disk_usage_ui(port)
            return
        except Exception as e:
            retries += 1
            log(f"❌ Attempt {retries}/{MAX_RETRIES} failed for sending {filename} to port {port}: {e}")
            if retries == MAX_RETRIES:
                log(f"⚠️ Failed to send {filename} to port {port} after {MAX_RETRIES} retries.")

def retrieve_file_from_server(port, filename):
    retries = 0
    while retries < MAX_RETRIES:
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
            store_metadata(filename, port, "client")
            update_disk_usage_ui(port)
            return data
        except Exception as e:
            retries += 1
            log(f"❌ Attempt {retries}/{MAX_RETRIES} failed for retrieving {filename} from port {port}: {e}")
            if retries == MAX_RETRIES:
                log(f"⚠️ Failed to retrieve {filename} from port {port} after {MAX_RETRIES} retries.")
                return None

def store_metadata(filename, src, dest):
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
    metadata[filename] = metadata.get(filename, [])
    metadata[filename].append({"from": src, "to": dest, "timestamp": time.ctime()})
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=4)

def merge_and_decrypt_files():
    merged = b''
    for filename in file_parts:
        index = file_parts.index(filename)
        main_port, replica_port = ports[index]
        port_to_use = choose_port(index)
        encrypted_data = retrieve_file_from_server(port_to_use, filename)
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

def update_disk_usage_ui(port):
    used, available = get_disk_space()
    space_label = f"Port {port} - Used: {used // (1024 ** 3)} GB, Available: {available // (1024 ** 3)} GB"
    if port == 8081:
        lbl_port1_space.set(space_label)
    elif port == 8082:
        lbl_port2_space.set(space_label)
    elif port == 8083:
        lbl_port3_space.set(space_label)

def send_and_reconstruct():
    if not selected_file:
        messagebox.showwarning("No file", "Please select a file.")
        return

    def process():
        global stop_animation
        stop_animation = False
        threading.Thread(target=animate_status, args=("🔁 Working",)).start()
        progress["value"] = 0
        generate_key()
        update_progress(15)
        time.sleep(0.5)

        split_and_encrypt_file()
        update_progress(30)
        time.sleep(0.5)

        for i in range(3):
            main_port, replica_port = ports[i]
            send_file_to_server(main_port, file_parts[i])
            send_file_to_server(replica_port, file_parts[i])
            update_progress(50 + (i+1)*10)
            time.sleep(0.5)

        merge_and_decrypt_files()
        update_progress(100)
        stop_animation = True
        lbl_status.set("✅ Done!")
        log("🎉 All operations completed successfully.")

    threading.Thread(target=process).start()

def animate_status(msg):
    i = 0
    while not stop_animation:
        lbl_status.set(msg + "." * (i % 4))
        time.sleep(0.5)
        i += 1

def update_progress(value):
    progress["value"] = value
    root.update_idletasks()

def reset_ui():
    global selected_file, stop_animation
    selected_file = ""
    lbl_file.set("No file selected.")
    lbl_key.set("")
    lbl_status.set("")
    txt_log.delete(1.0, END)
    progress["value"] = 0
    stop_animation = True
    log("🔄 Reset complete.")

def open_output_file():
    if os.path.exists(output_file):
        subprocess.Popen(["notepad", output_file])
    else:
        messagebox.showwarning("Missing", "No reconstructed file found.")

# Function to handle console commands
def handle_console_input(event=None):
    command = console_input.get("1.0", END).strip().lower()
    console_input.delete("1.0", END)
    if command == "generate_key":
        generate_key()
    elif command == "select_file":
        select_file()
    elif command == "split_by_nodes":
        split_and_encrypt_file()
    elif command == "distribute_file":
        send_and_reconstruct()
    elif command == "reconstruct_file":
        open_output_file()
    elif command == "reset_ui":
        reset_ui()
    elif command == "exit":
        log("Exiting...")
        root.quit()
    else:
        log(f"Unknown command: {command}")

root = Tk()
root.title("File Upload and Download System")

# GUI setup
frame = Frame(root)
frame.grid(row=0, column=0, padx=10, pady=10)

# Scrollable text log
txt_log = Text(frame, height=10, width=70)
txt_log.grid(row=0, column=0)

progress = ttk.Progressbar(frame, length=400, maximum=100, value=0)
progress.grid(row=1, column=0, pady=10)

console_input = Text(root, height=4, width=70)
console_input.grid(row=2, column=0)
console_input.bind("<Return>", handle_console_input)

root.mainloop()
