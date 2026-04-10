import os
import sys
from datetime import datetime

from src.metadata_recovery.superblock_parser import BtrfsSuperblockParser
from src.metadata_recovery.inode_parser import BtrfsInodeParser
from src.metadata_recovery.journal_analyzer import BtrfsJournalAnalyzer


class BtrfsMetadataRecovery:

    def __init__(self, image_path, output_dir="output/recovered_files"):
        # Convert to absolute paths (VERY IMPORTANT)
        self.image_path = os.path.abspath(image_path)
        self.output_dir = os.path.abspath(output_dir)

        self.superblock_parser = None
        self.inode_parser = None
        self.journal_analyzer = None
        self.recovered_files = []

    def run(self):
        print("=" * 60)
        print("  DEEP-RECOVERY : Btrfs Metadata Recovery Engine")
        print("=" * 60)
        print(f"  Image  : {self.image_path}")
        print(f"  Output : {self.output_dir}")
        print(f"  Time   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        os.makedirs(self.output_dir, exist_ok=True)

        if not self._step_superblock():
            print("[FATAL] Not a valid Btrfs image. Aborting.")
            return []

        self._step_inode_scan()
        self._step_journal_analysis()
        self._step_extract_files()
        self._print_summary()

        return self.recovered_files

    def _step_superblock(self):
        try:
            self.superblock_parser = BtrfsSuperblockParser(self.image_path)
            self.superblock_parser.read_superblock()
            self.superblock_parser.parse()

            print(self.superblock_parser.summary())
            return self.superblock_parser.validate()

        except Exception as e:
            print(f"[ERROR] Superblock parsing failed: {e}")
            return False

    def _step_inode_scan(self):
        sb = self.superblock_parser.parsed
        nodesize = sb.get("nodesize", 16384)

        self.inode_parser = BtrfsInodeParser(self.image_path, nodesize=nodesize)
        self.inode_parser.scan()

        print(f"[INFO] Inodes found: {len(self.inode_parser.inodes)}")

    def _step_journal_analysis(self):
        self.journal_analyzer = BtrfsJournalAnalyzer(self.image_path)
        self.journal_analyzer.analyze_superblock_copies()
        self.journal_analyzer.detect_generation_changes()
        self.journal_analyzer.find_orphan_inodes(self.inode_parser.inodes)

    def _step_extract_files(self):
        name_map = self.inode_parser.get_filename_map()
        inodes = self.inode_parser.inodes

        for oid, inode in inodes.items():
            if inode.file_type_str() == "RegularFile" and inode.size > 0:
                extents = self.inode_parser.get_extents_for_inode(oid)

                if not extents:
                    continue

                print(f"[+] Recovering inode {oid}")

                data = self._read_extents(extents, inode.size)

                if data:
                    name = name_map.get(oid, f"file_{oid}.bin")
                    out_path = os.path.join(self.output_dir, name)

                    with open(out_path, "wb") as f:
                        f.write(data)

                    self.recovered_files.append(out_path)

    def _read_extents(self, extents, expected_size):
        result = bytearray()

        try:
            with open(self.image_path, "rb") as f:
                for ext in extents:
                    if ext.extent_type == 0:
                        result.extend(ext.inline_data)

                    elif ext.extent_type in (1, 2):
                        f.seek(ext.disk_bytenr)
                        result.extend(f.read(ext.num_bytes))

        except Exception as e:
            print(f"[ERROR] Extent read failed: {e}")
            return None

        return bytes(result[:expected_size])

    def _print_summary(self):
        print("\n" + "=" * 60)
        print("RECOVERY SUMMARY")
        print("=" * 60)
        print(f"Recovered files: {len(self.recovered_files)}")

        for f in self.recovered_files:
            print(f" - {f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 -m src.metadata_recovery.recover <disk_image> [output_dir]")
        sys.exit(1)

    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/recovered_files"

    if not os.path.exists(image_path):
        print(f"[!] Error: File not found -> {image_path}")
        sys.exit(1)

    recovery = BtrfsMetadataRecovery(image_path, output_dir)
    recovery.run()


if __name__ == "__main__":
    main()