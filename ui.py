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
        self.root.geometry("1200x750")
        self.root.configure(bg="#1e1e1e")

        # allow resizing
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)

        # ---------- STYLE ----------
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 13, "bold"),
            padding=10
        )

        # ---------- TITLE ----------
        title = tk.Label(
            root,
            text="Deep Recovery System",
            font=("Segoe UI", 30, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        title.pack(pady=20)

        # ---------- BUTTON FRAME ----------
        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(pady=10)

        buttons = [

            ("Create Disk Image", self.create_image),
            ("Mount Disk", self.mount_disk),
            ("Unmount Disk", self.unmount_disk),

            ("Metadata Recovery", self.metadata_recovery),
            ("Deep Scan Recovery", self.deep_scan),
            ("Select Recovered Files", self.select_files),

            ("Generate Hashes", self.generate_hashes),
            ("Show Statistics", self.show_chart)
        ]

        for i, (text, cmd) in enumerate(buttons):

            btn = tk.Button(
                frame,
                text=text,
                command=lambda c=cmd: threading.Thread(target=c).start(),
                width=22,
                height=2,
                font=("Segoe UI", 13, "bold"),
                bg="#2d2d2d",
                fg="white",
                activebackground="#444444",
                bd=0
            )

            btn.grid(row=i // 4, column=i % 4, padx=12, pady=12)

        # ---------- PROGRESS BAR ----------
        self.progress = ttk.Progressbar(
            root,
            length=600,
            mode='indeterminate'
        )
        self.progress.pack(pady=15)

        # ---------- LOG TITLE ----------
        log_label = tk.Label(
            root,
            text="Recovery Log",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        log_label.pack()

        # ---------- LOG FRAME ----------
        log_frame = tk.Frame(root)
        log_frame.pack(fill="both", expand=True, padx=25, pady=10)

        scrollbar = tk.Scrollbar(log_frame)

        self.log_box = tk.Text(
            log_frame,
            bg="#000000",
            fg="#00ff9c",
            insertbackground="white",
            font=("Consolas", 16, "bold"),   # 🔥 BIGGER TEXT HERE
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(command=self.log_box.yview)

        scrollbar.pack(side="right", fill="y")
        self.log_box.pack(side="left", fill="both", expand=True)

    # ---------- LOG ----------
    def log(self, text):

        self.log_box.insert(tk.END, text + "\n\n")   # extra spacing
        self.log_box.see(tk.END)
        self.root.update()

    # ---------- CREATE IMAGE ----------
    def create_image(self):

        self.progress.start()
        self.log("Creating disk image...")

        os.makedirs("input", exist_ok=True)

        try:

            subprocess.run([
                "sudo",
                "dd",
                "if=/dev/sdb",
                "of=input/disk.img",
                "bs=4M",
                "status=progress"
            ])

            self.log("Disk image created: input/disk.img")

        except Exception as e:
            self.log(f"Error creating image: {e}")

        self.progress.stop()

    # ---------- MOUNT ----------
    def mount_disk(self):

        self.progress.start()
        self.log("Mounting disk image...")

        os.makedirs(MOUNT_DIR, exist_ok=True)

        try:

            subprocess.run([
                "sudo",
                "mount",
                "input/disk.img",
                MOUNT_DIR
            ])

            self.log(f"Mounted at {MOUNT_DIR}")

        except Exception as e:
            self.log(f"Mount error: {e}")

        self.progress.stop()

    # ---------- UNMOUNT ----------
    def unmount_disk(self):

        self.progress.start()
        self.log("Unmounting disk...")

        try:

            subprocess.run([
                "sudo",
                "umount",
                MOUNT_DIR
            ])

            self.log("Disk unmounted")

        except Exception as e:
            self.log(f"Unmount error: {e}")

        self.progress.stop()

    # ---------- METADATA RECOVERY ----------
    def metadata_recovery(self):

        global valid_files

        self.progress.start()
        self.log("Starting Metadata Recovery...")

        disk_image = "input/disk.img"

        if not os.path.exists(disk_image):

            self.log("ERROR: Disk image not found")
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

    # ---------- DEEP SCAN ----------
    def deep_scan(self):

        self.progress.start()
        self.log("Starting Deep Scan (PhotoRec)...")

        image = "input/disk.img"

        if not os.path.exists(image):

            self.log("Disk image not found")
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

    # ---------- SELECT FILES ----------
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

    # ---------- HASH FILE ----------
    def hash_file(self, filepath):

        sha256 = hashlib.sha256()

        try:

            with open(filepath, "rb") as f:

                while chunk := f.read(4096):
                    sha256.update(chunk)

            hash_val = sha256.hexdigest()

            self.log(f"{os.path.basename(filepath)} → SHA256: {hash_val}")

        except Exception as e:

            self.log(f"Hashing failed for {filepath}: {e}")

    # ---------- HASH ALL ----------
    def generate_hashes(self):

        self.log("Starting Hashing Process...")

        found = False

        for root_dir, dirs, files in os.walk(OUTPUT_DIR):

            for file in files:

                filepath = os.path.join(root_dir, file)

                self.hash_file(filepath)

                found = True

        if not found:
            self.log("No files found in output directory")

        self.log("Hashing Completed")

    # ---------- STATISTICS ----------
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
        chart.title("Recovery Statistics")

        canvas = FigureCanvasTkAgg(fig, chart)
        canvas.draw()
        canvas.get_tk_widget().pack()


# ---------- START UI ----------

root = tk.Tk()

app = DeepRecoveryUI(root)

root.mainloop()