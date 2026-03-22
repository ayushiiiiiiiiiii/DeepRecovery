import struct
import os
from datetime import datetime



# Btrfs Item Type Constants


BTRFS_INODE_ITEM_KEY     = 1
BTRFS_INODE_REF_KEY      = 12
BTRFS_DIR_ITEM_KEY       = 84
BTRFS_DIR_INDEX_KEY      = 96
BTRFS_EXTENT_DATA_KEY    = 108



BTRFS_HEADER_SIZE = 101              
BTRFS_KEY_SIZE    = 17               
BTRFS_ITEM_SIZE   = BTRFS_KEY_SIZE + 8 


BTRFS_INODE_ITEM_STRUCT_SIZE = 160


class BtrfsInodeItem:


    def __init__(self, objectid, raw_data):
        self.objectid = objectid
        self.raw = raw_data
        self.generation   = 0
        self.transid      = 0
        self.size         = 0
        self.nbytes       = 0
        self.block_group  = 0
        self.nlink        = 0
        self.uid          = 0
        self.gid          = 0
        self.mode         = 0
        self.rdev         = 0
        self.flags        = 0
        self.atime        = None
        self.ctime        = None
        self.mtime        = None
        self.otime        = None      # creation time
        self._parse()

    def _parse(self):
       
        if len(self.raw) < BTRFS_INODE_ITEM_STRUCT_SIZE:
            return

        (
            self.generation,
            self.transid,
            self.size,
            self.nbytes,
            self.block_group,
            self.nlink,
            self.uid,
            self.gid,
            self.mode,
        ) = struct.unpack_from("<QQQQQIIIi", self.raw, 0)

        self.rdev, self.flags = struct.unpack_from("<QQ", self.raw, 0x38)

        # Timestamps: each is (sec:uint64, nsec:uint32) = 12 bytes
        self.atime = self._parse_time(0x70)
        self.ctime = self._parse_time(0x7C)
        self.mtime = self._parse_time(0x88)
        self.otime = self._parse_time(0x94)

    def _parse_time(self, offset):
   
        if offset + 12 > len(self.raw):
            return None
        sec, nsec = struct.unpack_from("<QI", self.raw, offset)
        if sec == 0:
            return None
        try:
            return datetime.utcfromtimestamp(sec)
        except (OSError, OverflowError, ValueError):
            return None

    def file_type_str(self):
    
        ft = (self.mode >> 12) & 0xF
        types = {
            0x1: "FIFO", 0x2: "CharDev", 0x4: "Directory",
            0x6: "BlockDev", 0x8: "RegularFile", 0xA: "Symlink",
            0xC: "Socket",
        }
        return types.get(ft, f"Unknown(0x{ft:X})")

    def __repr__(self):
        return (
            f"Inode(oid={self.objectid}, type={self.file_type_str()}, "
            f"size={self.size}, nlink={self.nlink}, gen={self.generation}, "
            f"mtime={self.mtime})"
        )


class BtrfsDirItem:
  

    def __init__(self, raw_data):
        self.child_objectid = 0
        self.child_type     = 0
        self.name           = ""
        self._parse(raw_data)

    def _parse(self, data):
       
        if len(data) < 0x1E:
            return
        self.child_objectid = struct.unpack_from("<Q", data, 0)[0]
        self.child_type     = data[8]
        name_len            = struct.unpack_from("<H", data, 0x1B)[0]
        dir_type            = data[0x1D]
        if 0x1E + name_len <= len(data):
            self.name = data[0x1E:0x1E + name_len].decode("utf-8", errors="replace")

    def __repr__(self):
        return f"DirItem(name='{self.name}', child_oid={self.child_objectid})"


class BtrfsExtentData:


    def __init__(self, objectid, offset_in_file, raw_data):
        self.objectid       = objectid
        self.offset_in_file = offset_in_file  # byte offset within the file
        self.generation     = 0
        self.ram_bytes      = 0
        self.compression    = 0
        self.encryption     = 0
        self.other_encoding = 0
        self.extent_type    = 0               # 0=inline, 1=regular, 2=prealloc
        # For regular/prealloc extents:
        self.disk_bytenr    = 0               # physical byte offset on disk
        self.disk_num_bytes = 0
        self.extent_offset  = 0
        self.num_bytes      = 0
        # For inline extents:
        self.inline_data    = b""
        self._parse(raw_data)

    def _parse(self, data):
        
        if len(data) < 0x15:
            return
        (
            self.generation,
            self.ram_bytes,
            self.compression,
            self.encryption,
        ) = struct.unpack_from("<QQBb", data, 0)
        self.other_encoding = struct.unpack_from("<H", data, 0x12)[0]
        self.extent_type    = data[0x14]

        if self.extent_type == 0:
            # Inline extent – data follows immediately
            self.inline_data = data[0x15:]
        elif len(data) >= 0x35:
            (
                self.disk_bytenr,
                self.disk_num_bytes,
                self.extent_offset,
                self.num_bytes,
            ) = struct.unpack_from("<QQQQ", data, 0x15)

    def __repr__(self):
        if self.extent_type == 0:
            return f"ExtentData(oid={self.objectid}, inline, {len(self.inline_data)} bytes)"
        return (
            f"ExtentData(oid={self.objectid}, disk=0x{self.disk_bytenr:X}, "
            f"size={self.num_bytes})"
        )


class BtrfsInodeParser:
   

    def __init__(self, image_path, nodesize=16384):
    
        self.image_path = image_path
        self.nodesize   = nodesize
        self.inodes     = {}      # objectid → BtrfsInodeItem
        self.dir_items  = []      # list of BtrfsDirItem
        self.extents    = []      # list of BtrfsExtentData

   
    # Public API
  

    def scan(self, max_bytes=None):
        
        file_size = os.path.getsize(self.image_path)
        scan_limit = min(file_size, max_bytes) if max_bytes else file_size

        print(f"[*] Scanning for Btrfs inodes in {self.image_path}")
        print(f"    Image size : {file_size / (1024*1024):.2f} MB")
        print(f"    Node size  : {self.nodesize} bytes")
        print(f"    Scan limit : {scan_limit / (1024*1024):.2f} MB")

        with open(self.image_path, "rb") as f:
            offset = 0
            nodes_found = 0

            while offset + self.nodesize <= scan_limit:
                f.seek(offset)
                node_data = f.read(self.nodesize)
                if len(node_data) < self.nodesize:
                    break

                if self._is_leaf_node(node_data):
                    count = self._parse_leaf_node(node_data, offset)
                    if count > 0:
                        nodes_found += 1

                offset += self.nodesize

        print(f"[+] Scan complete: {nodes_found} leaf nodes, "
              f"{len(self.inodes)} inodes, {len(self.dir_items)} dir items, "
              f"{len(self.extents)} extent items")
        return self.inodes

    def get_filename_map(self):
       
        name_map = {}
        for d in self.dir_items:
            if d.name and d.child_objectid:
                name_map[d.child_objectid] = d.name
        return name_map

    def get_extents_for_inode(self, objectid):
        return [e for e in self.extents if e.objectid == objectid]


    # Internal helpers


    def _is_leaf_node(self, data):
        
        if len(data) < BTRFS_HEADER_SIZE:
            return False

        nritems = struct.unpack_from("<I", data, 0x60)[0]
        level   = data[0x64]

        if level != 0:
            return False
        if nritems == 0 or nritems > 500:
            return False

       
        if BTRFS_HEADER_SIZE + BTRFS_ITEM_SIZE <= len(data):
            first_item_type = data[BTRFS_HEADER_SIZE + 8]  # type byte in key
            if first_item_type > 230:
                return False

        return True

    def _parse_leaf_node(self, data, node_offset):
        nritems = struct.unpack_from("<I", data, 0x60)[0]
        count = 0

        for i in range(nritems):
            item_offset = BTRFS_HEADER_SIZE + i * BTRFS_ITEM_SIZE
            if item_offset + BTRFS_ITEM_SIZE > len(data):
                break

            
            objectid = struct.unpack_from("<Q", data, item_offset)[0]
            item_type = data[item_offset + 8]
            key_offset = struct.unpack_from("<Q", data, item_offset + 9)[0]
            data_offset = struct.unpack_from("<I", data, item_offset + 17)[0]
            data_size   = struct.unpack_from("<I", data, item_offset + 21)[0]

            # data_offset is relative to the end of the header
            abs_data_pos = BTRFS_HEADER_SIZE + data_offset
            if abs_data_pos + data_size > len(data):
                continue

            item_data = data[abs_data_pos:abs_data_pos + data_size]

            if item_type == BTRFS_INODE_ITEM_KEY and data_size >= BTRFS_INODE_ITEM_STRUCT_SIZE:
                inode = BtrfsInodeItem(objectid, item_data)
                self.inodes[objectid] = inode
                count += 1

            elif item_type == BTRFS_DIR_ITEM_KEY and data_size >= 0x1E:
                dir_item = BtrfsDirItem(item_data)
                if dir_item.name:
                    self.dir_items.append(dir_item)
                    count += 1

            elif item_type == BTRFS_EXTENT_DATA_KEY and data_size >= 0x15:
                extent = BtrfsExtentData(objectid, key_offset, item_data)
                self.extents.append(extent)
                count += 1

        return count



# Stand-alone usage

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python inode_parser.py <disk_image> [nodesize]")
        sys.exit(1)

    img = sys.argv[1]
    ns  = int(sys.argv[2]) if len(sys.argv) > 2 else 16384

    parser = BtrfsInodeParser(img, nodesize=ns)
    inodes = parser.scan()

    print("\n--- Discovered Inodes ---")
    name_map = parser.get_filename_map()
    for oid, inode in sorted(inodes.items()):
        name = name_map.get(oid, "(unknown)")
        print(f"  {inode}  name={name}")

    print(f"\n--- Extent Data Items ({len(parser.extents)}) ---")
    for ext in parser.extents[:20]:
        print(f"  {ext}")
