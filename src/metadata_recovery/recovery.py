import os

IMAGE_PATH = "input/disk_btrfs.img"
OUTPUT_DIR = "output"

# File signatures for carving
FILE_SIGNATURES = {
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG",
    "pdf": b"%PDF",
    "mp3": b"ID3",
    "zip": b"PK\x03\x04"
}

MAX_FILE_SIZE = 5000000  # 5MB chunk extraction


# Create output folder
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def metadata_recovery():
    print("\n===== METADATA BASED RECOVERY =====")

    recovered = 0

    with open(IMAGE_PATH, "rb") as f:

        data = f.read()

        # simple detection of text files stored inline
        if b".txt" in data:

            parts = data.split(b".txt")

            for i in range(len(parts) - 1):

                filename = "recovered_metadata_" + str(i) + ".txt"

                content = parts[i][-50:] + b".txt" + parts[i+1][:200]

                path = os.path.join(OUTPUT_DIR, filename)

                with open(path, "wb") as out:
                    out.write(content)

                print("Recovered metadata file:", filename)

                recovered += 1

    print("Metadata files recovered:", recovered)


def signature_recovery():

    print("\n===== SIGNATURE BASED RECOVERY =====")

    counts = {}

    for ext in FILE_SIGNATURES:
        counts[ext] = 0

    with open(IMAGE_PATH, "rb") as disk:

        data = disk.read()
        size = len(data)

        print("Scanning disk image:", size, "bytes")

        i = 0

        while i < size:

            for ext, sig in FILE_SIGNATURES.items():

                if data[i:i+len(sig)] == sig:

                    filename = f"recovered_{counts[ext]}.{ext}"
                    filepath = os.path.join(OUTPUT_DIR, filename)

                    print("Found", ext.upper(), "file at offset", i)

                    with open(filepath, "wb") as out:
                        out.write(data[i:i+MAX_FILE_SIZE])

                    counts[ext] += 1

            i += 1

    print("\nRecovered files summary:")

    for ext in counts:
        print(ext.upper(), ":", counts[ext])


def main():

    if not os.path.exists(IMAGE_PATH):
        print("Disk image not found:", IMAGE_PATH)
        return

    metadata_recovery()

    signature_recovery()

    print("\nRecovery complete. Files saved in 'output/' folder.")


if __name__ == "__main__":
    main()