import tkinter as tk
from tkinter import messagebox
import subprocess  # Used to run other Python files
import sys

# Predefined correct id and password
CORRECT_ID = "admin"
CORRECT_PASS = "1234"

def check_login():
    if node_type.get() == "Master":
        user_id = entry_id.get()
        password = entry_pass.get()

        if user_id == CORRECT_ID and password == CORRECT_PASS:
            messagebox.showinfo("Login Successful", "Welcome!")

            # Start s1.py servers in background
            subprocess.Popen([sys.executable, "s1.py", "8081"])
            subprocess.Popen([sys.executable, "s1.py", "8082"])
            subprocess.Popen([sys.executable, "s1.py", "8083"])

            root.destroy()  # Close the login window

            # Now open adv3_ui.py
            subprocess.run([sys.executable, "adv3_ui.py"])
        else:
            messagebox.showerror("Login Failed", "Incorrect ID or Password.")

    elif node_type.get() == "Slave":
        # Slave node - directly open slave_ui.py to see available files
        root.destroy()
        subprocess.run([sys.executable, "slave_ui.py"])

    else:
        messagebox.showwarning("Node Type Missing", "Please select a node type (Master or Slave).")

# Tkinter login window
root = tk.Tk()
root.title("Node Selection and Login")
root.geometry("300x300")
root.resizable(False, False)

# Node selection
tk.Label(root, text="Select Node Type:", font=("Arial", 12)).pack(pady=5)

node_type = tk.StringVar()

tk.Radiobutton(root, text="Master", variable=node_type, value="Master", font=("Arial", 11)).pack()
tk.Radiobutton(root, text="Slave", variable=node_type, value="Slave", font=("Arial", 11)).pack()

# ID and Password fields
tk.Label(root, text="User ID:", font=("Arial", 12)).pack(pady=5)
entry_id = tk.Entry(root, font=("Arial", 12))
entry_id.pack(pady=5)

tk.Label(root, text="Password:", font=("Arial", 12)).pack(pady=5)
entry_pass = tk.Entry(root, show="*", font=("Arial", 12))
entry_pass.pack(pady=5)

# Login button
tk.Button(root, text="Proceed", command=check_login, font=("Arial", 12), bg="green", fg="white").pack(pady=10)

root.mainloop()
