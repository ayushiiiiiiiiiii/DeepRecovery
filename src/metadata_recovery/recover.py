import sys
import os
import subprocess


def detect_filesystem(image_path):
    """
    Detect filesystem type using the `file` command.
    """

    try:
        result = subprocess.check_output(["file", image_path]).decode().lower()

        if "ext2" in result or "ext3" in result or "ext4" in result:
            return "ext"

        if "btrfs" in result:
            return "btrfs"

        return "unknown"

    except Exception as e:
        print(f"[ERROR] Failed to detect filesystem: {e}")
        return "unknown"


# ---------------------------------------------------------
# EXT METADATA RECOVERY
# ---------------------------------------------------------

def recover_ext(image_path, output_dir):

    print("[INFO] EXT filesystem detected")
    print("[INFO] Starting EXT metadata recovery...")

    os.makedirs(output_dir, exist_ok=True)

    try:

        # Use debugfs to list metadata
        result = subprocess.run(
            [
                "sudo",
                "debugfs",
                "-R",
                "ls -l",
                image_path
            ],
            capture_output=True,
            text=True
        )

        metadata_file = os.path.join(output_dir, "ext_metadata.txt")

        with open(metadata_file, "w") as f:
            f.write(result.stdout)

        print(f"[INFO] Metadata saved to {metadata_file}")

    except Exception as e:
        print(f"[ERROR] EXT metadata recovery failed: {e}")


# ---------------------------------------------------------
# BTRFS METADATA RECOVERY
# ---------------------------------------------------------

def recover_btrfs(image_path, output_dir):

    print("[INFO] Btrfs filesystem detected")
    print("[INFO] Starting Btrfs metadata recovery...")

    try:

        from src.metadata_recovery.superblock_parser import BtrfsSuperblockParser

        parser = BtrfsSuperblockParser(image_path)

        if not parser.is_valid():

            print("[WARNING] Invalid Btrfs superblock")
            return

        parser.parse()

        print("[INFO] Btrfs metadata parsed successfully")

    except ImportError:
        print("[ERROR] Btrfs parser module not found")

    except Exception as e:
        print(f"[ERROR] Btrfs metadata recovery failed: {e}")


# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------

def main():

    if len(sys.argv) < 3:

        print("Usage:")
        print("python -m src.metadata_recovery.recover <disk_image> <output_dir>")
        sys.exit(1)

    disk_image = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(disk_image):

        print("[ERROR] Disk image not found")
        sys.exit(1)

    print(f"[INFO] Disk image: {disk_image}")

    fs_type = detect_filesystem(disk_image)

    print(f"[INFO] Detected filesystem: {fs_type}")

    if fs_type == "ext":

        recover_ext(disk_image, output_dir)

    elif fs_type == "btrfs":

        recover_btrfs(disk_image, output_dir)

    else:

        print("[WARNING] Unsupported filesystem type")


if __name__ == "__main__":
    main()