
"""Forensic file signatures (Headers and Footers) for carving."""

FILE_SIGNATURES = {
    # --- IMAGES ---
    'jpg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'max_size': 10 * 1024 * 1024, # 10MB
    },
    'png': {
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xaeB`\x82',
        'max_size': 10 * 1024 * 1024,
    },
    'gif': {
        'header': b'GIF89a',
        'footer': b'\x00\x3b',
        'max_size': 5 * 1024 * 1024,
    },
    'bmp': {
        'header': b'BM',
        'footer': b'', # Uses size in header
        'max_size': 10 * 1024 * 1024,
        'kind': 'header_size'
    },
    'webp': {
        'header': b'RIFF',
        'kind': 'riff_webp',
        'max_size': 10 * 1024 * 1024,
    },

    # --- DOCUMENTS ---
    'pdf': {
        'header': b'%PDF',
        'footer': b'%%EOF',
        'max_size': 20 * 1024 * 1024, # 20MB
    },
    'zip': {
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'footer_padding': 18,
        'max_size': 50 * 1024 * 1024, # 50MB
    },
    'docx': {
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'footer_padding': 18,
        'max_size': 20 * 1024 * 1024,
        'kind': 'zip_derived'
    },

    # --- MULTIMEDIA ---
    'mp4': {
        'header': b'\x00\x00\x00\x18ftyp',
        'footer': b'', # Continuous stream
        'max_size': 100 * 1024 * 1024, # 100MB
        'kind': 'header_only'
    },
    'avi': {
        'header': b'RIFF',
        # AVI signature at offset 8
        'kind': 'riff_avi', 
        'max_size': 100 * 1024 * 1024,
    },
    'mp3': {
        'header': b'ID3',
        'max_size': 15 * 1024 * 1024,
        'kind': 'header_only'
    },
    'wav': {
        'header': b'RIFF',
        'kind': 'riff_wav',
        'max_size': 100 * 1024 * 1024,
    },

    # --- ARCHIVES & LEGACY ---
    'doc': {
        'header': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'max_size': 20 * 1024 * 1024,
        'kind': 'header_only'
    },
    'rar': {
        'header': b'Rar!\x1a\x07\x00',
        'max_size': 50 * 1024 * 1024,
        'kind': 'header_only'
    },
    '7z': {
        'header': b'7z\xbc\xaf\x27\x1c',
        'max_size': 50 * 1024 * 1024,
        'kind': 'header_only'
    }
}
