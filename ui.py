import recovery
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os

import subprocess
def create_disk_image():
    messagebox.showinfo("Info", "Creating disk image...")
    subprocess.run(["sudo","dd","if=/dev/sdb","of=input/disk.img","bs=4M","status=progress"])

def mount_disk():
    messagebox.showinfo("Info", "Mounting disk image...")
    subprocess.run(["sudo","mount","input/disk_xfs.img","mount_point"])

def unmount_disk():
    messagebox.showinfo("Info", "Unmounting disk...")
    subprocess.run(["sudo","umount","mount_point"])

def recover_files():
    messagebox.showinfo("Info", "Starting recovery tool...")
    subprocess.run(["photorec"])

def choose_disk():
    file = filedialog.askopenfilename()
    selected_file.set(file)

# -------- UI WINDOW -------- #

root = tk.Tk()
root.title("Deep Recovery Tool")
root.geometry("500x450")
root.configure(bg="#1e1e1e")

title = tk.Label(
    root,
    text="Deep Recovery System",
    font=("Arial",22,"bold"),
    fg="white",
    bg="#1e1e1e"
)

title.pack(pady=20)

# Selected disk label
selected_file = tk.StringVar()

disk_label = tk.Label(
    root,
    textvariable=selected_file,
    fg="white",
    bg="#1e1e1e"
)

disk_label.pack(pady=5)

# Select disk button
browse_btn = tk.Button(
    root,
    text="Select Disk Image",
    width=25,
    command=choose_disk
)

browse_btn.pack(pady=10)

# Create disk image button
create_btn = tk.Button(
    root,
    text="Create Disk Image",
    width=25,
    height=2,
    bg="#4CAF50",
    fg="white",
    command=create_disk_image
)

create_btn.pack(pady=10)

# Mount disk button
mount_btn = tk.Button(
    root,
    text="Mount Disk",
    width=25,
    height=2,
    bg="#2196F3",
    fg="white",
    command=mount_disk
)

mount_btn.pack(pady=10)

# Unmount disk button
unmount_btn = tk.Button(
    root,
    text="Unmount Disk",
    width=25,
    height=2,
    bg="#9C27B0",
    fg="white",
    command=unmount_disk
)

unmount_btn.pack(pady=10)

# Recover files button
recover_btn = tk.Button(
    root,
    text="Recover Files",
    width=25,
    height=2,
    bg="#FF9800",
    fg="white",
    command=recover_files
)

recover_btn.pack(pady=20)

exit_btn = tk.Button(
    root,
    text="Exit",
    width=20,
    command=root.quit
)

exit_btn.pack(pady=10)

root.mainloop()
