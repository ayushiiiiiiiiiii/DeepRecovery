"""
Sector-based file carver: signature carving, WebP via RIFF size, optional MIME fallback.

Requires: Pillow, python-magic (and system libmagic where applicable).
"""

from __future__ import annotations

import logging
import importlib.util
import os
from typing import Any, Optional

def _ensure_magic_bin_on_path() -> None:
    """
    On Windows, `python-magic` relies on system libmagic resolution.
    Some environments install `python-magic-bin` (bundled DLL) but `magic`
    loader still can't locate `libmagic.dll` unless its directory is on PATH.
    """
    try:
        spec = importlib.util.find_spec("magic")
        if not spec or not spec.submodule_search_locations:
            return
        magic_dir = spec.submodule_search_locations[0]
        bundled_dir = os.path.join(magic_dir, "libmagic")
        dll_path = os.path.join(bundled_dir, "libmagic.dll")
        if os.path.isfile(dll_path):
            os.environ["PATH"] = bundled_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        # If we can't discover a bundled libmagic, fall through to the real import error.
        return


try:
    import magic  # type: ignore
except ImportError:
    _ensure_magic_bin_on_path()
    import magic  # type: ignore

from .signatures import FILE_SIGNATURES
from .utils import generate_csv_report, generate_path, validate_integrity

logger = logging.getLogger(__name__)

FALLBACK_CHUNK = 1024 * 1024

_IMAGE_EXTS = frozenset({'jpg', 'jpeg', 'png', 'webp'})


def _sector_ceil(end_pos: int, sector_size: int) -> int:
    return ((end_pos + sector_size - 1) // sector_size) * sector_size


def _carve_riff_webp(
    f,
    offset: int,
    sector: bytes,
    sigs: dict[str, Any],
    disk_size: int,
) -> Optional[bytes]:
    """
    WebP in RIFF: 'RIFF' + LE size + 'WEBP' + chunks.
    Total file size = 8 + uint32 at bytes 4-7 (RIFF chunk size field).
    """
    if len(sector) < 12:
        return None
    if sector[:4] != b'RIFF' or sector[8:12] != b'WEBP':
        return None
    chunk_rest = int.from_bytes(sector[4:8], 'little')
    if chunk_rest < 0:
        chunk_rest = 0
    file_len = 8 + chunk_rest
    file_len = min(file_len, sigs['max_size'], max(0, disk_size - offset))
    f.seek(offset)
    return f.read(file_len)


def run_carver_professional(
    disk_path: str,
    output_folder: str,
    sector_size: int = 512,
) -> int:
    """
    Scan a binary image sector-by-sector, carve known types, optional MIME fallback.

    Returns the number of files written. Advances the scan offset past each carved
    region so fallback mode does not re-emit overlapping windows.

    Raises:
        FileNotFoundError: if disk_path does not exist.
        ValueError: invalid arguments.
        OSError: unreadable disk_path or unwritable output_folder.
    """
    if sector_size < 1:
        raise ValueError('sector_size must be positive')
    if not os.path.isfile(disk_path):
        raise FileNotFoundError(disk_path)

    os.makedirs(output_folder, exist_ok=True)

    try:
        mime_detector = magic.Magic(mime=True)
    except Exception as e:
        raise RuntimeError(
            'python-magic could not be initialized; ensure libmagic is installed.'
        ) from e

    recovery_log: list[dict[str, Any]] = []
    recovery_count = 0
    disk_size = os.path.getsize(disk_path)

    with open(disk_path, 'rb') as f:
        offset = 0
        overlap = 32 
        while offset < disk_size:
            f.seek(offset)
            sector = f.read(sector_size + overlap)
            if not sector:
                break

            # Pick the earliest matching signature inside this window.
            best: tuple[int, str, dict[str, Any], int] | None = None
            for ext, sigs in FILE_SIGNATURES.items():
                # WebP is detected via RIFF+WEBP markers (not header/footer).
                if sigs.get('kind') == 'riff_webp':
                    if len(sector) >= 12:
                        for rel in range(0, len(sector) - 12 + 1):
                            if sector[rel : rel + 4] == b'RIFF' and sector[
                                rel + 8 : rel + 12
                            ] == b'WEBP':
                                start_offset = offset + rel
                                best = (
                                    (start_offset, ext, sigs, rel)
                                    if best is None or start_offset < best[0]
                                    else best
                                )
                                break
                    continue

                if 'header' not in sigs or 'footer' not in sigs:
                    continue
                header_pos = sector.find(sigs['header'])
                if header_pos == -1:
                    continue

                start_offset = offset + header_pos
                if best is None or start_offset < best[0]:
                    best = (start_offset, ext, sigs, header_pos)

            if best is not None:
                start_offset, ext, sigs, rel = best
                is_image = ext.lower() in _IMAGE_EXTS

                # WebP carve
                if sigs.get('kind') == 'riff_webp':
                    file_data = _carve_riff_webp(
                        f, start_offset, sector[rel:], sigs, disk_size
                    )
                    if file_data is not None:
                        is_valid = validate_integrity(file_data, f'.{ext}') if is_image else True
                        if is_image and is_valid:
                            status = 'Verified'
                        elif is_image:
                            status = 'Partial/Corrupt'
                        else:
                            status = 'Detected (RIFF/WEBP)'

                        recovery_count += 1
                        save_to = generate_path(
                            output_folder, ext, recovery_count, start_offset
                        )
                        with open(save_to, 'wb') as out:
                            out.write(file_data)
                        recovery_log.append({
                            'offset': start_offset,
                            'type': ext,
                            'path': save_to,
                            'status': status,
                        })
                        offset = start_offset + len(file_data)
                        continue
                    # RIFF/WEBP markers were seen, but we couldn't carve a bounded blob.
                    # Advance to avoid getting stuck on the same window.
                    offset = start_offset + 1
                    continue

                # Header/footer carve
                if 'header' in sigs and 'footer' in sigs:
                    max_carve = sigs['max_size']
                    f.seek(start_offset)

                    file_data = sector[rel:]
                    bytes_read = len(file_data)
                    found_footer = False

                    footer_pos = file_data.find(sigs['footer'])
                    if footer_pos != -1:
                        end = footer_pos + len(sigs['footer'])
                        file_data = file_data[:end]
                        found_footer = True
                        bytes_read = len(file_data)
                    else:
                        while bytes_read < max_carve:
                            remaining = min(sector_size, max_carve - bytes_read)
                            next_chunk = f.read(remaining)
                            if not next_chunk:
                                break

                            footer_pos = next_chunk.find(sigs['footer'])
                            if footer_pos != -1:
                                end_in_chunk = footer_pos + len(sigs['footer'])
                                file_data += next_chunk[:end_in_chunk]
                                found_footer = True
                                bytes_read = len(file_data)
                                break

                            file_data += next_chunk
                            bytes_read += len(next_chunk)

                    if found_footer:
                        if is_image and validate_integrity(file_data, f'.{ext}'):
                            status = 'Verified'
                        elif is_image:
                            status = 'Partial/Corrupt'
                        else:
                            status = 'Detected (Header/Footer)'

                        recovery_count += 1
                        save_to = generate_path(
                            output_folder, ext, recovery_count, start_offset
                        )
                        with open(save_to, 'wb') as out:
                            out.write(file_data)
                        recovery_log.append({
                            'offset': start_offset,
                            'type': ext,
                            'path': save_to,
                            'status': status,
                        })

                    # Always advance past the attempted region to keep scan progressing.
                    offset = start_offset + bytes_read
                    continue

            # No signature hit: MIME fallback on this window.
            try:
                file_description = mime_detector.from_buffer(sector)
            except Exception as exc:
                logger.warning('MIME detection failed at offset %s: %s', offset, exc)
                offset += sector_size
                continue

            if any(x in file_description for x in ['image/', 'application/', 'video/']):
                if 'octet-stream' not in file_description:
                    raw_ext = file_description.split('/')[-1].split('-')[-1]
                    f.seek(offset)
                    read_len = min(FALLBACK_CHUNK, disk_size - offset)
                    fallback_data = f.read(read_len)

                    recovery_count += 1
                    save_to = generate_path(output_folder, raw_ext, recovery_count, offset)
                    with open(save_to, 'wb') as out:
                        out.write(fallback_data)
                    recovery_log.append({
                        'offset': offset,
                        'type': raw_ext,
                        'path': save_to,
                        'status': 'Unverified (Auto)',
                    })

                    offset = offset + len(fallback_data)
                    continue

            offset += sector_size

    if recovery_log:
        csv_path = generate_csv_report(output_folder, recovery_log)
        logger.info('Carving report written: %s', csv_path)

    logger.info('Carving complete; files recovered: %s', recovery_count)
    return recovery_count
