import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import threading
import os
import hashlib
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

OUTPUT_DIR = "output"
MOUNT_DIR = "mount_point"

valid_files = 0
corrupted_files = 0


class DeepRecoveryUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Deep Recovery Tool")
        self.root.geometry("1000x650")
        self.root.configure(bg="#1e1e1e")

        title = tk.Label(
            root,
            text="Deep Recovery System",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        title.pack(pady=10)

        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(pady=10)

        ttk.Button(frame, text="Create Disk Image",
                   command=lambda: threading.Thread(target=self.create_image).start()).grid(row=0, column=0, padx=10)

        ttk.Button(frame, text="Mount Disk",
                   command=lambda: threading.Thread(target=self.mount_disk).start()).grid(row=0, column=1, padx=10)

        ttk.Button(frame, text="Unmount Disk",
                   command=lambda: threading.Thread(target=self.unmount_disk).start()).grid(row=0, column=2, padx=10)

        ttk.Button(frame, text="Metadata Recovery",
                   command=lambda: threading.Thread(target=self.metadata_recovery).start()).grid(row=1, column=0, pady=10)

        ttk.Button(frame, text="Deep Scan Recovery",
                   command=lambda: threading.Thread(target=self.deep_scan).start()).grid(row=1, column=1)

        ttk.Button(frame, text="Select Recovered Files",
                   command=self.select_files).grid(row=1, column=2)

        ttk.Button(frame, text="Generate Hashes",
                   command=lambda: threading.Thread(target=self.generate_hashes).start()).grid(row=1, column=3)

        ttk.Button(frame, text="Show Statistics",
                   command=self.show_chart).grid(row=1, column=4)

        self.progress = ttk.Progressbar(root, length=500, mode='indeterminate')
        self.progress.pack(pady=10)

        log_label = tk.Label(
            root,
            text="Recovery Log",
            font=("Arial", 14),
            fg="white",
            bg="#1e1e1e"
        )
        log_label.pack()

        self.log_box = tk.Text(
            root,
            height=20,
            width=120,
            bg="black",
            fg="lime"
        )
        self.log_box.pack(pady=10)

    # ---------------- LOG ----------------

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

    # ---------------- CREATE IMAGE ----------------

    def create_image(self):

        self.progress.start()
        self.log("Creating disk image...")

        os.makedirs("input", exist_ok=True)

        subprocess.run([
            "sudo",
            "dd",
            "if=/dev/sdb",
            "of=input/disk.img",
            "bs=4M",
            "status=progress"
        ])

        self.log("Disk image created at input/disk.img")
        self.progress.stop()

    # ---------------- MOUNT DISK ----------------

    def mount_disk(self):

        self.progress.start()
        self.log("Mounting disk image...")

        os.makedirs(MOUNT_DIR, exist_ok=True)

        subprocess.run([
            "sudo",
            "mount",
            "input/disk.img",
            MOUNT_DIR
        ])

        self.log("Disk mounted at mount_point")
        self.progress.stop()

    # ---------------- UNMOUNT ----------------

    def unmount_disk(self):

        self.progress.start()
        self.log("Unmounting disk...")

        subprocess.run([
            "sudo",
            "umount",
            MOUNT_DIR
        ])

        self.log("Disk unmounted")
        self.progress.stop()

    # ---------------- METADATA RECOVERY ----------------

    def metadata_recovery(self):

        global valid_files

        self.progress.start()
        self.log("Starting Metadata Recovery...")

        disk_image = "input/disk.img"

        if not os.path.exists(disk_image):

            self.log("ERROR: Disk image not found.")
            self.progress.stop()
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        process = subprocess.Popen(
            [
                "python3",
                "-m",
                "src.metadata_recovery.recover",
                disk_image,
                OUTPUT_DIR
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for line in process.stdout:
            self.log(line.strip())

            if "Recovered" in line or "recovered" in line:
                valid_files += 1

        self.log("Metadata Recovery Completed")
        self.progress.stop()

    # ---------------- DEEP SCAN ----------------

    def deep_scan(self):

        self.progress.start()
        self.log("Starting Deep Scan (PhotoRec)...")

        image = "input/disk.img"

        if not os.path.exists(image):

            self.log("Disk image not found!")
            self.progress.stop()
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        cmd = [
            "photorec",
            "/log",
            "/d", OUTPUT_DIR,
            "/cmd", image, "options,search"
        ]

        subprocess.run(cmd)

        self.log("Deep Scan Completed")

        webbrowser.open(os.path.abspath(OUTPUT_DIR))

        self.progress.stop()

    # ---------------- SELECT FILES ----------------

    def select_files(self):

        global valid_files

        files = filedialog.askopenfilenames(
            initialdir=OUTPUT_DIR,
            title="Select Recovered Files"
        )

        if not files:
            self.log("No files selected")
            return

        for file in files:

            self.log(file)
            valid_files += 1
            self.hash_file(file)

    # ---------------- HASH SINGLE FILE ----------------

    def hash_file(self, filepath):

        sha256 = hashlib.sha256()

        try:

            with open(filepath, "rb") as f:

                while True:

                    data = f.read(4096)

                    if not data:
                        break

                    sha256.update(data)

            hash_val = sha256.hexdigest()

            self.log(f"{os.path.basename(filepath)} → SHA256: {hash_val}")

        except Exception as e:

            self.log(f"Hashing failed for {filepath}: {e}")

    # ---------------- HASH ALL FILES ----------------

    def generate_hashes(self):

        self.log("Starting Hashing Process...\n")

        found = False

        for root_dir, dirs, files in os.walk(OUTPUT_DIR):

            for file in files:

                filepath = os.path.join(root_dir, file)

                self.hash_file(filepath)

                found = True

        if not found:
            self.log("No files found in output directory")

        self.log("\nHashing Completed\n")

    # ---------------- STATISTICS ----------------

    def show_chart(self):

        global valid_files, corrupted_files

        if valid_files == 0 and corrupted_files == 0:
            corrupted_files = 1

        data = [valid_files, corrupted_files]
        labels = ["Valid Files", "Corrupted Files"]

        fig, ax = plt.subplots()
        ax.pie(data, labels=labels, autopct='%1.1f%%')
        ax.set_title("Recovery Statistics")

        chart = tk.Toplevel(self.root)

        canvas = FigureCanvasTkAgg(fig, chart)
        canvas.draw()
        canvas.get_tk_widget().pack()


# ---------------- START UI ----------------

root = tk.Tk()

app = DeepRecoveryUI(root)

root.mainloop()