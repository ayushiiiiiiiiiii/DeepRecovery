# Deep-Recovery

**Deep-Recovery** is a digital forensics and data recovery project designed to retrieve deleted files directly from raw disk images. This tool demonstrates advanced sector-level file carving alongside filesystem-specific metadata recovery techniques.

## 🎯 Objective
To recover deleted, corrupted, or lost files from disk images formatted with different file systems (XFS, BTRFS) without relying heavily on the operating system's native mounting utilities.

## ✨ Core Features
The recovery engine consists of three distinct modules that work together to maximize data extraction:

### 1. File Carving Engine (Raw Sector Recovery)
A highly professional, sector-by-sector file carver designed for scenarios where filesystem metadata is destroyed or overwritten.
* **Signature Recognition**: Precisely searches for `PDF`, `PNG`, `JPG`, and `WebP` (via RIFF chunks) by matching file headers and footers.
* **Intelligent Scanning**: Predicts and extracts files based on theoretical boundaries and utilizes robust overlapping sliding windows to defeat cross-sector fragmentation.
* **MIME-Type Fallback**: Features a built-in `python-magic` detection mechanism to identify unsupported file types.
* **Forensic Verification**: Automatically verifies retrieved images using `Pillow` and generates an organized `carving_report.csv` for forensic mapping.

### 2. Btrfs Metadata Recovery
A specialized module that targets the internal structures of the Btrfs filesystem.
* **Superblock & Inode Parsing**: Accurately maps files and directories directly from the Btrfs root tree.
* **Journal & Extent Analysis**: Discovers orphan inodes and deleted generation changes to find historical data that still resides on the disk.

### 3. Basic Disk Sweeping
* Includes [disk_reader.py](./disk_reader.py) for rapid, shallow block scanning visualization and immediate file type detection within random chunks.

---

## 💾 Disk Images Used
Two virtual disk images were created locally for rigorous testing:
- `disk_btrfs.img`
- `disk_xfs.img`
*(Note: These images are **not uploaded to GitHub** because they exceed the standard 100MB file limit).*

## 🛠️ Prerequisites
- **Python 3.8+**
- **libmagic**: Required for file type identification.
- **Dependencies**: Install via `pip install -r requirements.txt`.

---

## 🛠️ Development & Methodology

To ensure the accuracy of the recovery engine, a controlled forensic environment was created using standard Linux utilities.

### Tools Used for Image Creation
* **`dd`**: For allocating raw, zero-filled disk images.
* **`mkfs.btrfs` / `mkfs.xfs`**: For partitioning and formatting the virtual drives.
* **`mount` / `umount`**: For simulating real-world file system usage.
* **`shasum`**: For generating cryptographic hashes to verify data integrity.

### Steps Performed
1. **Infrastructure**: Created 256MB raw disk images (`.img`).
2. **Environment**: Formatted images with the Btrfs and XFS filesystems.
3. **Data Population**: Wrote test files (PDFs, JPEGs, PNGs) to the mounted drives.
4. **Deletion Simulation**: Deleted specific files and unmounted the drives to simulate data loss.
5. **Recovery Phase**: Ran **Deep-Recovery** modules to carve the raw sectors and parse the metadata to retrieve the deleted items.
6. **Validation**: Compared the recovered hashes against original file hashes.



## 🚀 Usage

### 1. Running the File Carver
Scan a disk image for common file types and save them to an output folder:
```bash
python -m src.carver.engine <disk_image> <output_folder>
```

### 2. Running Metadata Recovery (Btrfs)
Analyze Btrfs metadata to recover files with their original names and structures:
```bash
python -m src.metadata_recovery.recover <disk_image> [output_dir]
```


