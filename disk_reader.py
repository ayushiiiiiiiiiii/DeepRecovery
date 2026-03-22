def read_blocks(file_path, block_size=1024):
    block_number = 1

    try:
        with open(file_path, "rb") as file:

            print("Starting disk scan...\n")
            found_types = set()

            while True:
                block = file.read(block_size)
                file.seek(-100, 1)
                if not block:
                    break

                if b"%PDF" in block and "PDF" not in found_types:
                    print(f"PDF found in block {block_number}")
                    found_types.add("PDF")

                if b"\x89PNG\r\n\x1a\n" in block and "PNG" not in found_types:
                    print(f"PNG found in block {block_number}")
                    found_types.add("PNG")

                if b"\xff\xd8\xff" in block and "JPG" not in found_types:
                    print(f"JPG found in block {block_number}")
                    found_types.add("JPG")

                if (b"ID3" in block or b"\xff\xfb" in block) and "MP3" not in found_types:
                    print(f"MP3 found in block {block_number}")
                    found_types.add("MP3")

                if b"ftyp" in block and "MP4" not in found_types:
                    print(f"MP4 found in block {block_number}")
                    found_types.add("MP4")

                if block_number <= 5:
                    print(f"Reading block{block_number},size={len(block)}")

                yield block_number, block

                block_number += 1

        print("\nScan completed.")

    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    file_path = "input/disk_btrfs.img"

    for block in read_blocks(file_path):
        pass