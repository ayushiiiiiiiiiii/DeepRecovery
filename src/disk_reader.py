import os

def scan_disk(image_path, block_size=4096):
    block_number = 0
    found_types = set()

    try:
        with open(image_path, "rb") as file:
            print(" Starting disk scan...\n")

            while True:
                block = file.read(block_size)
                if not block:
                    break

                block_number += 1

                # -------- PDF --------
                if b"%PDF" in block:
                    print(f"[+] PDF detected at block {block_number}")
                    found_types.add("PDF")

                # -------- JPG -------
                if b"\xff\xd8\xff" in block:
                    print(f"[+] JPG detected at block {block_number}")
                    found_types.add("JPG")

                # -------- MP3 ------
                if b"ID3" in block:
                    print(f"[+] MP3 detected at block {block_number}")
                    found_types.add("MP3")

                # -------- MP4 -------
                if b"ftyp" in block:
                    print(f"[+] MP4 detected at block {block_number}")
                    found_types.add("MP4")

            print("\n Scan complete!")
            print(" File types found:", ", ".join(found_types) if found_types else "None")

    except FileNotFoundError:
        print(" File not found. Check path!")
    except Exception as e:
        print("Error:", e)


# -------- RUN --------
if __name__ == "__main__":
    image_path = input("Enter disk image path: ")
    scan_disk(image_path)