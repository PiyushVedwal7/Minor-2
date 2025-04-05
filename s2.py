# server_dual.py (can be used on any port like 8081, 8082, etc.)
import socket
import threading
import os

SERVER_IP = "127.0.0.1"
SERVER_PORT = 8082  # change as needed per instance
STORAGE_DIR = f"server_storage_{SERVER_PORT}"
os.makedirs(STORAGE_DIR, exist_ok=True)

def handle_client(conn):
    try:
        request_type = conn.recv(3).decode()

        if request_type == "PUT":
            name_len = int.from_bytes(conn.recv(4), byteorder='big')
            file_name = conn.recv(name_len).decode()
            file_size = int.from_bytes(conn.recv(4), byteorder='big')
            file_data = b''
            while len(file_data) < file_size:
                file_data += conn.recv(4096)
            with open(os.path.join(STORAGE_DIR, file_name), 'wb') as f:
                f.write(file_data)
            print(f"✅ Received file {file_name}")

        elif request_type == "GET":
            name_len = int.from_bytes(conn.recv(4), byteorder='big')
            file_name = conn.recv(name_len).decode()
            file_path = os.path.join(STORAGE_DIR, file_name)

            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    data = f.read()
                conn.send(len(data).to_bytes(4, byteorder='big'))
                conn.send(data)
                print(f"📤 Sent file {file_name}")
            else:
                conn.send((0).to_bytes(4, byteorder='big'))
                print(f"❌ File {file_name} not found")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((SERVER_IP, SERVER_PORT))
        server.listen()
        print(f"🚀 Server ready on {SERVER_IP}:{SERVER_PORT}")
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()
