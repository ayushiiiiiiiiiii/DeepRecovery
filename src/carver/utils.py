"""Helpers for validation, output paths, and reporting."""

from __future__ import annotations

import csv
import io
import os
from typing import Any

from PIL import Image

_IMAGE_EXTS = frozenset({'.jpg', '.jpeg', '.png', '.webp'})


def validate_integrity(data: bytes, ext: str) -> bool:
    """Verify image bytes with Pillow where supported; other types are not validated here."""
    if ext.lower() not in _IMAGE_EXTS:
        return True
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        return True
    except OSError:
        return False


def generate_path(output_dir: str, ext: str, count: int, offset: int) -> str:
    """Place carved files under type-based subfolders."""
    categories = {
        'jpg': 'Images',
        'jpeg': 'Images',
        'png': 'Images',
        'gif': 'Images',
        'bmp': 'Images',
        'webp': 'Images',
        'pdf': 'Documents',
        'docx': 'Documents',
        'doc': 'Documents',
        'mp3': 'Audio',
        'wav': 'Audio',
        'mp4': 'Video',
        'avi': 'Video',
        'zip': 'Archives',
        'rar': 'Archives',
        '7z': 'Archives',
    }
    subfolder = categories.get(ext.lower(), 'Misc')
    final_dir = os.path.join(output_dir, subfolder)
    os.makedirs(final_dir, exist_ok=True)
    return os.path.join(final_dir, f'carved_{offset}_{count:04d}.{ext}')


def generate_csv_report(output_dir: str, recovery_data: list[dict[str, Any]]) -> str:
    """Write a simple forensic-style CSV next to carved output."""
    report_path = os.path.join(output_dir, 'carving_report.csv')
    headers = [
        'Evidence ID',
        'Disk Offset (Bytes)',
        'File Type',
        'Verification Status',
        'Saved Path',
    ]
    with open(report_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for i, entry in enumerate(recovery_data, 1):
            writer.writerow({
                'Evidence ID': f'EV-{i:04d}',
                'Disk Offset (Bytes)': entry['offset'],
                'File Type': entry['type'],
                'Verification Status': entry['status'],
                'Saved Path': entry['path'],
            })
    return report_path
