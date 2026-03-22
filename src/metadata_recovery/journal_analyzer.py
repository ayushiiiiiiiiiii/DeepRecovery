import struct
import os

from .superblock_parser import (
    BtrfsSuperblockParser,
    BTRFS_SUPERBLOCK_OFFSET,
    BTRFS_SUPERBLOCK_MIRROR_1,
    BTRFS_SUPERBLOCK_MIRROR_2,
    BTRFS_MAGIC,
)


class BtrfsJournalAnalyzer:

    SUPERBLOCK_OFFSETS = [
        ("Primary",  BTRFS_SUPERBLOCK_OFFSET),
        ("Mirror 1", BTRFS_SUPERBLOCK_MIRROR_1),
        ("Mirror 2", BTRFS_SUPERBLOCK_MIRROR_2),
    ]

    def __init__(self, image_path):
        self.image_path = image_path
        self.superblocks = []
        self.orphan_inodes = []

    def analyze_superblock_copies(self):
        file_size = os.path.getsize(self.image_path)
        self.superblocks = []

        for name, offset in self.SUPERBLOCK_OFFSETS:
            if offset + 4096 > file_size:
                print(f"  [{name}] Offset 0x{offset:X} beyond image size, skipping")
                continue

            parser = BtrfsSuperblockParser(self.image_path)
            raw = parser.read_superblock(offset)
            if raw is None:
                continue

            parsed = parser.parse()
            if parsed and parser.validate():
                self.superblocks.append({
                    "name": name,
                    "offset": offset,
                    "generation": parsed.get("generation", 0),
                    "root": parsed.get("root", 0),
                    "chunk_root": parsed.get("chunk_root", 0),
                    "log_root": parsed.get("log_root", 0),
                    "log_root_transid": parsed.get("log_root_transid", 0),
                    "total_bytes": parsed.get("total_bytes", 0),
                    "bytes_used": parsed.get("bytes_used", 0),
                    "uuid": parser.get_uuid(),
                })
                print(f"  [{name}] Valid Btrfs superblock at 0x{offset:X}, "
                      f"generation={parsed.get('generation', '?')}")
            else:
                print(f"  [{name}] No valid Btrfs superblock at 0x{offset:X}")

        return self.superblocks

    def detect_generation_changes(self):
        if len(self.superblocks) < 2:
            return []

        changes = []
        primary = self.superblocks[0]

        for sb in self.superblocks[1:]:
            gen_diff = primary["generation"] - sb["generation"]
            if gen_diff != 0:
                changes.append({
                    "primary_gen": primary["generation"],
                    "mirror_name": sb["name"],
                    "mirror_gen": sb["generation"],
                    "diff": gen_diff,
                    "older_root": sb["root"],
                    "newer_root": primary["root"],
                })
                print(f"  [!] Generation mismatch: Primary(gen={primary['generation']}) "
                      f"vs {sb['name']}(gen={sb['generation']}), diff={gen_diff}")

        if not changes:
            print("  [=] All superblock copies have the same generation")

        return changes

    def find_orphan_inodes(self, inodes):
        self.orphan_inodes = []

        for oid, inode in inodes.items():
            if inode.nlink == 0 and inode.size > 0:
                self.orphan_inodes.append(inode)
                print(f"  [ORPHAN] Inode {oid}: size={inode.size}, "
                      f"type={inode.file_type_str()}, gen={inode.generation}")

        print(f"  [*] Found {len(self.orphan_inodes)} orphan inode(s)")
        return self.orphan_inodes

    def find_old_tree_roots(self):
        if len(self.superblocks) < 2:
            return []

        current_root = self.superblocks[0]["root"]
        old_roots = []

        for sb in self.superblocks[1:]:
            if sb["root"] != current_root and sb["root"] != 0:
                old_roots.append(sb["root"])
                print(f"  [OLD ROOT] {sb['name']} has old root at "
                      f"0x{sb['root']:X} (current: 0x{current_root:X})")

        return old_roots

    def summary(self):
        lines = [
            "=" * 60,
            "       BTRFS JOURNAL / GENERATION ANALYSIS",
            "=" * 60,
        ]

        if not self.superblocks:
            lines.append("  No valid superblocks found.")
            return "\n".join(lines)

        lines.append(f"  Superblock copies found : {len(self.superblocks)}")
        for sb in self.superblocks:
            lines.append(
                f"    {sb['name']:10s}  gen={sb['generation']}  "
                f"root=0x{sb['root']:X}  log_root=0x{sb['log_root']:X}"
            )

        if len(self.superblocks) >= 2:
            gens = [sb["generation"] for sb in self.superblocks]
            if len(set(gens)) == 1:
                lines.append(f"  Generation status     : All copies at gen {gens[0]}")
            else:
                lines.append(f"  Generation status     : MISMATCH detected")
                for sb in self.superblocks:
                    lines.append(f"    {sb['name']:10s}  generation = {sb['generation']}")

        lines.append(f"  Orphan inodes found   : {len(self.orphan_inodes)}")
        for inode in self.orphan_inodes[:10]:
            lines.append(
                f"    oid={inode.objectid}  size={inode.size}  "
                f"type={inode.file_type_str()}  gen={inode.generation}"
            )

        lines.append("=" * 60)
        return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python journal_analyzer.py <disk_image>")
        sys.exit(1)

    analyzer = BtrfsJournalAnalyzer(sys.argv[1])

    print("\n[*] Analyzing superblock copies...")
    analyzer.analyze_superblock_copies()

    print("\n[*] Checking generation differences...")
    analyzer.detect_generation_changes()

    print(analyzer.summary())