
import sys
import os

def hex_dump(filename, length=256):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    print(f"\n--- Forensic Hex Dump: {os.path.basename(filename)} ---")
    print("Offset    Hex                                        ASCII")
    print("-" * 70)

    try:
        with open(filename, 'rb') as f:
            chunk = f.read(length)
            for i in range(0, len(chunk), 16):
                sub_chunk = chunk[i:i+16]
                
                # Hex part
                hex_part = ' '.join(f"{b:02x}" for b in sub_chunk)
                hex_part = hex_part.ljust(47)
                
                # ASCII part
                ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in sub_chunk)
                
                print(f"{i:08x}  {hex_part}  |{ascii_part}|")
    except Exception as e:
        print(f"Error reading file: {e}")
    print("-" * 70 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hex_viewer.py <filename>")
    else:
        hex_dump(sys.argv[1])
