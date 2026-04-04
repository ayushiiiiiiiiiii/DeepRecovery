import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

class RecoveryUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Deep Recovery Tool")
        self.root.geometry("650x500")

        self.disk_path = ""

        title = tk.Label(root, text="Deep Recovery System", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        # Select Disk Image
        self.select_btn = tk.Button(root, text="Select Disk Image", command=self.select_disk)
        self.select_btn.pack(pady=5)

        self.disk_label = tk.Label(root, text="No disk selected")
        self.disk_label.pack()

        # Recovery options
        option_label = tk.Label(root, text="Select Recovery Type", font=("Arial", 12))
        option_label.pack(pady=10)

        self.recovery_type = tk.StringVar()
        self.recovery_type.set("metadata")

        meta_btn = tk.Radiobutton(root, text="Metadata Recovery", variable=self.recovery_type, value="metadata")
        meta_btn.pack()

        deep_btn = tk.Radiobutton(root, text="Deep Scan Recovery", variable=self.recovery_type, value="deep")
        deep_btn.pack()

        # Buttons
        self.recover_btn = tk.Button(root, text="Recover Files", command=self.recover_files, bg="green", fg="white")
        self.recover_btn.pack(pady=10)

        self.mount_btn = tk.Button(root, text="Mount Disk", command=self.mount_disk)
        self.mount_btn.pack(pady=5)

        self.exit_btn = tk.Button(root, text="Exit", command=root.quit)
        self.exit_btn.pack(pady=10)

        # Log box
        log_label = tk.Label(root, text="Recovery Logs")
        log_label.pack()

        self.log_box = tk.Text(root, height=12, width=70)
        self.log_box.pack()

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

    def select_disk(self):
        path = filedialog.askopenfilename(filetypes=[("Disk Images", "*.img *.bin")])

        if path:
            self.disk_path = path
            self.disk_label.config(text=path)
            self.log("Disk selected: " + path)

    def mount_disk(self):

        if self.disk_path == "":
            messagebox.showerror("Error", "Select disk image first")
            return

        cmd = f"sudo mount -o loop {self.disk_path} mount_point/"

        try:
            subprocess.run(cmd, shell=True)
            self.log("Disk mounted successfully")

        except Exception as e:
            self.log(str(e))

    def recover_files(self):

        if self.disk_path == "":
            messagebox.showerror("Error", "Select disk image first")
            return

        recovery_method = self.recovery_type.get()

        if recovery_method == "metadata":

            self.log("Starting Metadata Recovery...")

            try:
                subprocess.run(["python3","src/metadata_recovery/superblock_parser.py",self.disk_path])
                subprocess.run(["python3","src/metadata_recovery/inode_parser.py",self.disk_path])
                subprocess.run(["python3","src/metadata_recovery/recovery.py",self.disk_path])

                self.log("Metadata recovery completed")

            except Exception as e:
                self.log(str(e))


        elif recovery_method == "deep":

            self.log("Starting Deep Scan Recovery...")

            try:
                subprocess.run(["python3","src/disk_reader.py",self.disk_path])

                self.log("Deep recovery completed")

            except Exception as e:
                self.log(str(e))


if __name__ == "__main__":

    root = tk.Tk()
    app = RecoveryUI(root)
    root.mainloop()