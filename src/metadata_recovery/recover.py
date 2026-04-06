import os

IMAGE_PATH = "input/disk_btrfs.img"
OUTPUT_DIR = "output"

FILE_SIGNATURES = {
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG",
    "pdf": b"%PDF",
    "mp3": b"ID3",
    "zip": b"PK\x03\x04"
}

FILE_ENDINGS = {
    "jpg": b"\xff\xd9",
    "png": b"IEND\xae\x42\x60\x82",
    "pdf": b"%%EOF",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB fallback cap

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def find_end(data, start, ext):
    """Find the real end of a file using its closing signature."""
    if ext not in FILE_ENDINGS:
        return start + MAX_FILE_SIZE
    end_sig = FILE_ENDINGS[ext]
    pos = data.find(end_sig, start)
    if pos == -1:
        return start + MAX_FILE_SIZE
    return pos + len(end_sig)


def metadata_recovery():
    """
    Metadata-based recovery using the Btrfs engine.
    This replaces the old broken approach that just grabbed random bytes around '.txt'.
    """
    print("\n===== METADATA BASED RECOVERY =====")
    try:
        from metadata_recovery.recover import BtrfsMetadataRecovery
        recovery = BtrfsMetadataRecovery(IMAGE_PATH, os.path.join(OUTPUT_DIR, "metadata"))
        recovered = recovery.run()
        print(f"Metadata recovery complete. Files recovered: {len(recovered)}")
        return recovered
    except ImportError:
        print("[!] Btrfs metadata engine not found. Skipping metadata recovery.")
        return []
    except Exception as e:
        print(f"[!] Metadata recovery error: {e}")
        return []


def signature_recovery():
    """
    Signature-based (file carving) recovery.
    Finds file headers, then locates the real end marker so the file is not padded with garbage.
    """
    print("\n===== SIGNATURE BASED RECOVERY =====")

    sig_output = os.path.join(OUTPUT_DIR, "signature")
    if not os.path.exists(sig_output):
        os.makedirs(sig_output)

    counts = {ext: 0 for ext in FILE_SIGNATURES}

    with open(IMAGE_PATH, "rb") as disk:
        data = disk.read()

    size = len(data)
    print(f"Scanning disk image: {size} bytes")

    i = 0
    while i < size:
        matched = False
        for ext, sig in FILE_SIGNATURES.items():
            if data[i:i + len(sig)] == sig:
                end = find_end(data, i, ext)
                end = min(end, i + MAX_FILE_SIZE)  # safety cap

                filename = f"recovered_{counts[ext]}.{ext}"
                filepath = os.path.join(sig_output, filename)

                print(f"  Found {ext.upper()} at offset {i}, "
                      f"size {end - i} bytes -> {filename}")

                with open(filepath, "wb") as out:
                    out.write(data[i:end])

                counts[ext] += 1
                i = end  # jump past this file, avoid re-scanning its body
                matched = True
                break

        if not matched:
            i += 1

    print("\nRecovered files summary:")
    for ext, count in counts.items():
        print(f"  {ext.upper()}: {count}")


def main():
    if not os.path.exists(IMAGE_PATH):
        print(f"Disk image not found: {IMAGE_PATH}")
        return

    metadata_recovery()
    signature_recovery()

    print("\nRecovery complete.")
    print(f"  Metadata files -> {OUTPUT_DIR}/metadata/")
    print(f"  Signature files -> {OUTPUT_DIR}/signature/")


if __name__ == "__main__":
    main()
