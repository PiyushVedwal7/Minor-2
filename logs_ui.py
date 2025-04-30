import tkinter as tk
from tkinter import Listbox, StringVar, Frame
import os
import json

# --- Root Window Setup ---
root = tk.Tk()
root.title("Transfer Log Search")
root.geometry("600x500")
root.config(bg="#ffffff")

# --- Log Search UI ---

# Create a frame for the search UI
search_frame = Frame(root, bg="#ffffff")
search_frame.pack(pady=20)

# Add a header label
header_label = tk.Label(search_frame, text="🔍 Search Transfer Logs by Filename", font=("Segoe UI", 14, 'bold'), bg="#ffffff", fg="#333333")
header_label.pack(pady=10)

# Search entry field with rounded corners and padding
log_search_var = StringVar()
log_search_entry = tk.Entry(search_frame, textvariable=log_search_var, width=50, font=("Segoe UI", 12), relief="solid", bd=2)
log_search_entry.pack(pady=10)

# Create a Scrollbar for the Listbox
scrollbar = tk.Scrollbar(search_frame, orient="vertical")

# Log listbox with custom styling
log_listbox = Listbox(search_frame, width=80, height=10, font=("Courier New", 11), yscrollcommand=scrollbar.set, selectmode=tk.SINGLE, bg="#f8f8f8", bd=2, relief="groove")
log_listbox.pack(pady=10)
scrollbar.config(command=log_listbox.yview)
scrollbar.pack(side="right", fill="y")

# --- Functions ---

def load_transfer_logs():
    log_listbox.delete(0, tk.END)
    keyword = log_search_var.get().lower()
    transfer_log_file = "transfer_log.json"  # Change to your actual log file path
    if os.path.exists(transfer_log_file):
        with open(transfer_log_file, "r") as f:
            logs = json.load(f)
        found_logs = [entry for entry in logs if keyword in entry['filename'].lower()]
        if found_logs:
            for entry in found_logs:
                line = f"{entry['timestamp']} | {entry['filename']} -> {entry['port']}"
                log_listbox.insert(tk.END, line)
        else:
            log_listbox.insert(tk.END, "No logs found matching the search term.")
    else:
        log_listbox.insert(tk.END, "Transfer logs file does not exist.")

# Bind the search field to dynamically update the log list
log_search_var.trace_add("write", lambda *args: load_transfer_logs())

# --- Mainloop ---
root.mainloop()
