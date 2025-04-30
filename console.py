import tkinter as tk
import os
from tkinter import simpledialog, messagebox

# Fixed slave folders and their corresponding passwords
SLAVE_FOLDERS = {
    "storage_8081": "password1",
    "storage_8082": "password2",
    "storage_8083": "password3",
}

def list_files(folder_name):
    listbox.delete(0, tk.END)  # Clear previous

    if not os.path.exists(folder_name):
        listbox.insert(tk.END, f"Folder '{folder_name}' does not exist.")
        return

    for item in os.listdir(folder_name):
        item_path = os.path.join(folder_name, item)
        if os.path.isdir(item_path):
            listbox.insert(tk.END, f"[Folder] {item}")
        else:
            listbox.insert(tk.END, f"[File] {item}")

def on_folder_select(event):
    selected_index = folder_listbox.curselection()
    if selected_index:
        selected_folder = SLAVE_FOLDERS.keys()[selected_index[0]]  # Get the folder name
        folder_password = SLAVE_FOLDERS[selected_folder]  # Get the password for the selected folder
        
        # Ask for password
        entered_password = simpledialog.askstring("Password", f"Enter password for {selected_folder}:",
                                                  show="*")
        
        if entered_password == folder_password:
            list_files(selected_folder)
        else:
            messagebox.showerror("Access Denied", "Incorrect password for this folder.")

# Tkinter window
root = tk.Tk()
root.title("Slave Node - View Split Files")
root.geometry("600x400")
root.resizable(False, False)

tk.Label(root, text="Select a Slave Folder to View Files", font=("Arial", 16)).pack(pady=10)

# Folder selection listbox
folder_listbox = tk.Listbox(root, width=40, height=3, font=("Arial", 12))
for folder in SLAVE_FOLDERS.keys():
    folder_listbox.insert(tk.END, folder)
folder_listbox.pack(pady=10)
folder_listbox.bind('<<ListboxSelect>>', on_folder_select)

# Files display listbox
listbox = tk.Listbox(root, width=60, height=15, font=("Arial", 10))
listbox.pack(pady=10)

root.mainloop()
