import socket
from cryptography.fernet import Fernet
import os

# Define server ports
ports = [8081, 8082, 8083]
host = "127.0.0.1"

# File names
original_file = "sample.txt"
file_parts = ["client_part1.dat", "client_part2.dat", "client_part3.dat"]
output_file = "reconstructed_sample.txt"

# Generate and save encryption key
key = Fernet.generate_key()
with open("encryption.key", "wb") as kf:
    kf.write(key)
fernet = Fernet(key)

# 1. Split and encrypt
def split_and_encrypt_file():
    with open(original_file, "rb") as f:
        data = f.read()

    part_size = len(data) // 3
    parts = [data[:part_size], data[part_size:part_size*2], data[part_size*2:]]

    for i in range(3):
        encrypted = fernet.encrypt(parts[i])
        with open(file_parts[i], "wb") as pf:
            pf.write(encrypted)
    print("🔐 File split and encrypted.")

# 2. Send part to server
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
        print(f"✅ Sent {filename} to {host}:{port}")
    except Exception as e:
        print(f"❌ Error sending {filename} to {host}:{port}: {e}")

# 3. Retrieve part from server
def retrieve_file_from_server(port, filename):
    try:
        s = socket.socket()
        s.connect((host, port))
        s.send(b"GET")
        s.send(len(filename.encode()).to_bytes(4, 'big'))
        s.send(filename.encode())

        size = int.from_bytes(s.recv(4), 'big')
        if size == 0:
            print(f"⚠️ {filename} not found on {host}:{port}")
            return None

        data = b''
        while len(data) < size:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        s.close()
        print(f"📥 Retrieved {filename} from {host}:{port}")
        return data
    except Exception as e:
        print(f"❌ Error retrieving {filename} from {host}:{port}: {e}")
        return None

# 4. Merge decrypted parts
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
                print(f"❌ Decryption failed for {filename}: {e}")
                return
        else:
            return

    with open(output_file, "wb") as out:
        out.write(merged)
    print(f"✅ File reconstructed as {output_file}")

# 🔁 Main Process
if __name__ == "__main__":
    split_and_encrypt_file()

    for i in range(3):
        send_file_to_server(ports[i], file_parts[i])

    print("📤 All parts sent. Retrieving and reconstructing...")

    merge_and_decrypt_files()
