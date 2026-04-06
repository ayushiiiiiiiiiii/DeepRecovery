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
=======
import sys
import struct
from datetime import datetime

from .superblock_parser import BtrfsSuperblockParser
from .inode_parser import BtrfsInodeParser
from .journal_analyzer import BtrfsJournalAnalyzer


class BtrfsMetadataRecovery:

    def __init__(self, image_path, output_dir="output/recovered_files"):
        self.image_path = image_path
        self.output_dir = output_dir
        self.superblock_parser = None
        self.inode_parser = None
        self.journal_analyzer = None
        self.recovered_files = []

    def run(self):
        print("=" * 60)
        print("  DEEP-RECOVERY : Btrfs Metadata Recovery Engine")
        print("  Member 4 – Metadata Recovery Module")
        print("=" * 60)
        print(f"  Image  : {self.image_path}")
        print(f"  Output : {self.output_dir}")
        print(f"  Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        os.makedirs(self.output_dir, exist_ok=True)

        print("\n" + "-" * 40)
        print("[STEP 1] Parsing Btrfs Superblock")
        print("-" * 40)
        if not self._step_superblock():
            print("[FATAL] Not a valid Btrfs image. Aborting.")
            return []

        print("\n" + "-" * 40)
        print("[STEP 2] Scanning for Inodes and Metadata")
        print("-" * 40)
        self._step_inode_scan()

        print("\n" + "-" * 40)
        print("[STEP 3] Journal / Generation Analysis")
        print("-" * 40)
        self._step_journal_analysis()

        print("\n" + "-" * 40)
        print("[STEP 4] Extracting File Data via Metadata Pointers")
        print("-" * 40)
        self._step_extract_files()

        self._print_summary()

        return self.recovered_files

    def _step_superblock(self):
        self.superblock_parser = BtrfsSuperblockParser(self.image_path)
        self.superblock_parser.read_superblock()
        self.superblock_parser.parse()

        print(self.superblock_parser.summary())

        return self.superblock_parser.validate()

    def _step_inode_scan(self):
        sb = self.superblock_parser.parsed
        nodesize = sb.get("nodesize", 16384)

        self.inode_parser = BtrfsInodeParser(self.image_path, nodesize=nodesize)
        self.inode_parser.scan()

        name_map = self.inode_parser.get_filename_map()
        inodes = self.inode_parser.inodes

        if inodes:
            print(f"\n  Discovered {len(inodes)} inode(s):")
            for oid, inode in sorted(inodes.items()):
                name = name_map.get(oid, "(unknown)")
                print(f"    oid={oid:6d}  {inode.file_type_str():14s}  "
                      f"size={inode.size:>10d}  nlink={inode.nlink}  "
                      f"name={name}")
        else:
            print("  No inodes found in scan.")

        if self.inode_parser.extents:
            print(f"\n  Discovered {len(self.inode_parser.extents)} extent data item(s):")
            for ext in self.inode_parser.extents[:15]:
                print(f"    {ext}")

    def _step_journal_analysis(self):
        self.journal_analyzer = BtrfsJournalAnalyzer(self.image_path)

        print("\n  Analyzing superblock copies...")
        self.journal_analyzer.analyze_superblock_copies()

        print("\n  Checking generation differences...")
        self.journal_analyzer.detect_generation_changes()

        print("\n  Scanning for orphan inodes (deleted files)...")
        self.journal_analyzer.find_orphan_inodes(self.inode_parser.inodes)

        print(self.journal_analyzer.summary())

    def _step_extract_files(self):
        name_map = self.inode_parser.get_filename_map()
        inodes = self.inode_parser.inodes

        recovery_candidates = []

        for oid, inode in inodes.items():
            if inode.file_type_str() == "RegularFile" and inode.size > 0:
                extents = self.inode_parser.get_extents_for_inode(oid)
                if extents:
                    recovery_candidates.append((oid, inode, extents))

        if not recovery_candidates:
            print("  No files with extent data found for recovery.")
            print("  (File data may have been overwritten or metadata is incomplete)")
            return

        print(f"  Found {len(recovery_candidates)} file(s) with extent data")

        for oid, inode, extents in recovery_candidates:
            name = name_map.get(oid, f"recovered_inode_{oid}")
            deleted = " [DELETED]" if inode.nlink == 0 else ""
            print(f"\n  Recovering: {name} (oid={oid}, size={inode.size}){deleted}")

            recovered_data = self._read_extents(extents, inode.size)

            if recovered_data:
                out_path = os.path.join(self.output_dir, name)
                if os.path.exists(out_path):
                    base, ext = os.path.splitext(name)
                    out_path = os.path.join(self.output_dir, f"{base}_{oid}{ext}")

                with open(out_path, "wb") as f:
                    f.write(recovered_data)

                actual_size = len(recovered_data)
                print(f"    -> Saved to {out_path} ({actual_size} bytes)")
                self.recovered_files.append(out_path)
            else:
                print(f"    -> Could not extract data")

    def _read_extents(self, extents, expected_size):
        sorted_extents = sorted(extents, key=lambda e: e.offset_in_file)
        result = bytearray()

        try:
            with open(self.image_path, "rb") as f:
                for ext in sorted_extents:
                    if ext.extent_type == 0:
                        result.extend(ext.inline_data)

                    elif ext.extent_type in (1, 2) and ext.disk_bytenr > 0:
                        read_offset = ext.disk_bytenr + ext.extent_offset
                        read_size = ext.num_bytes

                        if read_size == 0 or read_size > 100 * 1024 * 1024:
                            continue

                        f.seek(read_offset)
                        data = f.read(read_size)
                        result.extend(data)
                    else:
                        if ext.num_bytes > 0:
                            result.extend(b"\x00" * ext.num_bytes)

        except Exception as e:
            print(f"    [!] Error reading extents: {e}")
            return None

        if len(result) > expected_size:
            result = result[:expected_size]

        return bytes(result) if result else None

    def _print_summary(self):
        print("\n" + "=" * 60)
        print("       RECOVERY SUMMARY")
        print("=" * 60)

        sb = self.superblock_parser.parsed
        print(f"  Filesystem UUID   : {self.superblock_parser.get_uuid() or 'N/A'}")
        print(f"  Generation        : {sb.get('generation', 'N/A')}")
        print(f"  Inodes found      : {len(self.inode_parser.inodes)}")
        print(f"  Dir entries found : {len(self.inode_parser.dir_items)}")
        print(f"  Extent items      : {len(self.inode_parser.extents)}")
        print(f"  Orphan inodes     : {len(self.journal_analyzer.orphan_inodes)}")
        print(f"  Files recovered   : {len(self.recovered_files)}")

        if self.recovered_files:
            print(f"\n  Recovered files saved to: {self.output_dir}/")
            for path in self.recovered_files:
                size = os.path.getsize(path) if os.path.exists(path) else 0
                print(f"    {os.path.basename(path):30s}  {size:>10d} bytes")
        else:
            print("\n  No files recovered via metadata pointers.")

        print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m metadata_recovery.recover <disk_image> [output_dir]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/recovered_files"

    if not os.path.exists(image_path):
        print(f"[!] Error: Image file not found: {image_path}")
        sys.exit(1)

    recovery = BtrfsMetadataRecovery(image_path, output_dir)
    recovered = recovery.run()

    sys.exit(0 if recovered else 1)


if __name__ == "__main__":
    main()

