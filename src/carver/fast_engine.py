import os
import re
import logging
import struct
from typing import List, Dict, Any
from collections import defaultdict

from .signatures import FILE_SIGNATURES
from .utils import generate_csv_report, generate_path, validate_integrity

logger = logging.getLogger(__name__)

# --- HYBRID PERFORMANCE SETTINGS (v1.2) ---
BLOCK_SIZE = 40 * 1024 * 1024  # 40 MB per read (10x Faster)
OVERLAP_SIZE = 8 * 1024 * 1024 # 8 MB overlap

def run_carver_turbo(disk_path: str, output_folder: str) -> int:
    """
    Hybrid High Performance Engine (Regex Lookup + Original Stable Extraction)
    """
    if not os.path.isfile(disk_path):
        raise FileNotFoundError(disk_path)

    os.makedirs(output_folder, exist_ok=True)
    recovery_log: List[Dict[str, Any]] = []
    recovery_count = 0
    disk_size = os.path.getsize(disk_path)
    
    # Pre-compile signature 'Radar' for single-pass detection
    unique_headers = list({s['header'] for s in FILE_SIGNATURES.values() if 'header' in s})
    radar_regex = re.compile(b"|".join(re.escape(h) for h in unique_headers))

    with open(disk_path, 'rb') as f:
        offset = 0
        while offset < disk_size:
            f.seek(offset)
            buffer = f.read(BLOCK_SIZE + OVERLAP_SIZE)
            if not buffer: break
            
            # 1. HIGH-SPEED LOOKUP (Find NEXT possible file in one pass)
            match = radar_regex.search(buffer)
            if not match:
                offset += BLOCK_SIZE
                continue

            rel_pos = match.start()
            header_bytes = match.group()
            start_disk_offset = offset + rel_pos
            
            # 2. ROBUST EXTRACTION (Original Logic)
            # Find which file type matched (Original Loop but only at rel_pos)
            best_ext = None
            best_sigs = None
            for ext, sigs in FILE_SIGNATURES.items():
                if buffer.startswith(sigs['header'], rel_pos):
                    # Multi-type check (WebP/Docx/Avi)
                    if ext in ['webp', 'avi', 'wav'] and len(buffer) >= rel_pos + 12:
                        marker = buffer[rel_pos+8:rel_pos+12]
                        if ext == 'webp' and marker != b'WEBP': continue
                        if ext == 'avi' and marker != b'AVI ': continue
                        if ext == 'wav' and marker != b'WAVE': continue
                    
                    best_ext = ext
                    best_sigs = sigs
                    break

            if best_ext:
                safe_ext = best_ext if best_ext not in ['dosexec', 'zlib', 'elf'] else 'dat'
                
                # Check for footer (Original Robust Scan)
                footer_sig = best_sigs.get('footer', b'')
                footer_pos = -1
                if footer_sig:
                    footer_pos = buffer.find(footer_sig, rel_pos + len(best_sigs['header']))
                
                if footer_pos != -1:
                    # Accurate Cut
                    padding = best_sigs.get('footer_padding', 0)
                    file_end_rel = footer_pos + len(footer_sig) + padding
                    file_data = buffer[rel_pos:file_end_rel]
                    
                    status = "Verified" if validate_integrity(file_data, f".{best_ext}") else "Carved"
                    recovery_count += 1
                    save_path = generate_path(output_folder, safe_ext, recovery_count, start_disk_offset)
                    with open(save_path, 'wb') as out: out.write(file_data)
                    recovery_log.append({'offset': start_disk_offset, 'type': safe_ext, 'path': save_path, 'status': status})
                    offset = start_disk_offset + len(file_data)
                    continue
                else:
                    # Fallback Extraction
                    read_len = best_sigs.get('max_size', 5*1024*1024)
                    is_valid = True
                    
                    if best_ext == 'bmp' and len(buffer) >= rel_pos + 6:
                        try:
                            bmp_size = struct.unpack('<I', buffer[rel_pos+2:rel_pos+6])[0]
                            # BMP size sanity check
                            if 14 < bmp_size <= best_sigs.get('max_size', 50*1024*1024): 
                                read_len = bmp_size
                                status = "Extracted (Smart Size)"
                            else: 
                                is_valid = False
                        except: is_valid = False

                    if best_ext in ['avi', 'wav', 'webp'] and len(buffer) >= rel_pos + 8:
                        import struct
                        try:
                            riff_size = struct.unpack('<I', buffer[rel_pos+4:rel_pos+8])[0] + 8
                            if 12 < riff_size <= read_len: read_len = riff_size
                            else: is_valid = False
                        except: is_valid = False
                            
                    if not is_valid:
                        offset = start_disk_offset + 2
                        continue

                    f.seek(start_disk_offset)
                    file_data = f.read(min(read_len, disk_size - start_disk_offset))
                    
                    recovery_count += 1
                    save_path = generate_path(output_folder, safe_ext, recovery_count, start_disk_offset)
                    with open(save_path, 'wb') as out: out.write(file_data)
                    recovery_log.append({'offset': start_disk_offset, 'type': safe_ext, 'path': save_path, 'status': status or "Extracted (Fallback)"})
                    
                    if read_len == best_sigs.get('max_size'):
                        offset = start_disk_offset + 1024
                    else:
                        offset = start_disk_offset + len(file_data)
                    continue

            offset += BLOCK_SIZE

    if recovery_log:
        generate_csv_report(output_folder, recovery_log)
    return recovery_count

    if recovery_log:
        generate_csv_report(output_folder, recovery_log)
    return recovery_count
