
import struct
import uuid
import os


# Constants


BTRFS_SUPERBLOCK_OFFSET = 0x10000       
BTRFS_SUPERBLOCK_MIRROR_1 = 0x4000000    
BTRFS_SUPERBLOCK_MIRROR_2 = 0x4000000000 

BTRFS_MAGIC = b"_BHRfS_M"             
BTRFS_SUPERBLOCK_SIZE = 4096

class BtrfsSuperblockParser:
   

    FIELD_FORMATS = {
        "csum":                 (0x00, "32s"),
        "fsid":                 (0x20, "16s"),
        "bytenr":               (0x30, "<Q"),
        "flags":                (0x38, "<Q"),
        "magic":                (0x40, "8s"),
        "generation":           (0x48, "<Q"),
        "root":                 (0x50, "<Q"),
        "chunk_root":           (0x58, "<Q"),
        "log_root":             (0x60, "<Q"),
        "log_root_transid":     (0x68, "<Q"),
        "total_bytes":          (0x70, "<Q"),
        "bytes_used":           (0x78, "<Q"),
        "root_dir_objectid":    (0x80, "<Q"),
        "num_devices":          (0x88, "<Q"),
        "sectorsize":           (0x90, "<I"),
        "nodesize":             (0x94, "<I"),
        "leafsize":             (0x98, "<I"),
        "stripesize":           (0x9C, "<I"),
        "sys_chunk_array_size": (0xA0, "<I"),
        "label":                (0x12B, "256s"),
    }

    def __init__(self, image_path):
        
        self.image_path = image_path
        self.raw_superblock = None
        self.parsed = {}


    # Public API
   

    def read_superblock(self, offset=BTRFS_SUPERBLOCK_OFFSET):
        
        file_size = os.path.getsize(self.image_path)
        if offset + BTRFS_SUPERBLOCK_SIZE > file_size:
            print(f"[!] Image too small for superblock at offset 0x{offset:X}")
            return None

        with open(self.image_path, "rb") as f:
            f.seek(offset)
            self.raw_superblock = f.read(BTRFS_SUPERBLOCK_SIZE)

        return self.raw_superblock

    def parse(self):
        
        if self.raw_superblock is None:
            self.read_superblock()
        if self.raw_superblock is None:
            return None

        for field_name, (offset, fmt) in self.FIELD_FORMATS.items():
            size = struct.calcsize(fmt)
            if offset + size > len(self.raw_superblock):
                continue
            raw_value = struct.unpack_from(fmt, self.raw_superblock, offset)
          
            self.parsed[field_name] = raw_value[0]

        return self.parsed

    def validate(self):
    
        if not self.parsed:
            self.parse()
        if not self.parsed:
            return False
        return self.parsed.get("magic") == BTRFS_MAGIC

    def get_uuid(self):
       
        fsid = self.parsed.get("fsid")
        if fsid and len(fsid) == 16:
            return str(uuid.UUID(bytes=fsid))
        return None

    def get_label(self):
        
        raw = self.parsed.get("label")
        if raw:
            return raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")
        return ""

    def summary(self):
       
        if not self.parsed:
            self.parse()
        if not self.parsed:
            return "[!] No superblock data available."

        valid = self.validate()
        p = self.parsed
        total_mb = p.get("total_bytes", 0) / (1024 * 1024)
        used_mb = p.get("bytes_used", 0) / (1024 * 1024)

        lines = [
            "=" * 60,
            "       BTRFS SUPERBLOCK ANALYSIS",
            "=" * 60,
            f"  Magic            : {p.get('magic', b'').decode(errors='replace')}",
            f"  Valid Btrfs       : {'YES' if valid else 'NO'}",
            f"  UUID              : {self.get_uuid() or 'N/A'}",
            f"  Label             : {self.get_label() or '(none)'}",
            f"  Generation        : {p.get('generation', 'N/A')}",
            f"  Total Size        : {total_mb:.2f} MB",
            f"  Bytes Used        : {used_mb:.2f} MB",
            f"  Sector Size       : {p.get('sectorsize', 'N/A')} bytes",
            f"  Node Size         : {p.get('nodesize', 'N/A')} bytes",
            f"  Num Devices       : {p.get('num_devices', 'N/A')}",
            f"  Root Tree Addr    : 0x{p.get('root', 0):X}",
            f"  Chunk Tree Addr   : 0x{p.get('chunk_root', 0):X}",
            f"  Log Tree Addr     : 0x{p.get('log_root', 0):X}",
            f"  Log Root TransID  : {p.get('log_root_transid', 'N/A')}",
            "=" * 60,
        ]
        return "\n".join(lines)



# Stand-alone usage

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python superblock_parser.py <disk_image>")
        sys.exit(1)

    parser = BtrfsSuperblockParser(sys.argv[1])
    parser.read_superblock()
    parser.parse()
    print(parser.summary())
