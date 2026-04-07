import os
import shutil

def run_cross_mapper(carve_dir, metadata_map, output_dir, log_callback=None):
    """
    Matches carved files (generic names) with original metadata (names and sizes).
    """
    os.makedirs(output_dir, exist_ok=True)
    matched_count = 0
    remaining_metadata = dict(metadata_map)
    
    if log_callback:
        log_callback(f"Starting Cross-Mapper on {len(remaining_metadata)} metadata entries...")

    for root, dirs, files in os.walk(carve_dir):
        for f in files:
            if f.endswith('.csv') or f.endswith('.txt'):
                continue
                
            c_path = os.path.join(root, f)
            try:
                c_size = os.path.getsize(c_path)
            except OSError:
                continue
            c_ext = f.split('.')[-1].lower() if '.' in f else ''
            
            # Match by exact size and extension
            match_found = False
            for og_name, og_size in list(remaining_metadata.items()):
                og_ext = og_name.split('.')[-1].lower() if '.' in og_name else ''
                
                if og_ext == c_ext and og_size == c_size:
                    final_path = os.path.join(output_dir, og_name)
                    
                    if os.path.exists(final_path):
                        base, ext = os.path.splitext(og_name)
                        final_path = os.path.join(output_dir, f"{base}_alt_{matched_count}{ext}")
                        
                    shutil.copy2(c_path, final_path)
                    matched_count += 1
                    del remaining_metadata[og_name]
                    match_found = True
                    break
                    
    if log_callback:
        log_callback(f"Cross-Mapper healed {matched_count} files with original names.")
        
    return matched_count
