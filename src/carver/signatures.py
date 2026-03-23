"""
Known file signatures for header/footer carving.

WebP uses RIFF container length (see engine) instead of a footer search.
"""

FILE_SIGNATURES = {
    'jpg': {
        'header': b'\xff\xd8\xff',
        'footer': b'\xff\xd9',
        'max_size': 15 * 1024 * 1024,
        'name': 'JPEG Image',
    },
    'png': {
        'header': b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a',
        'footer': b'\x49\x45\x4e\x44\xae\x42\x60\x82',
        'max_size': 20 * 1024 * 1024,
        'name': 'PNG Image',
    },
    'pdf': {
        'header': b'\x25\x50\x44\x46',
        'footer': b'\x25\x25\x45\x4f\x46',
        'max_size': 50 * 1024 * 1024,
        'name': 'PDF Document',
    },
    'webp': {
        'kind': 'riff_webp',
        'max_size': 10 * 1024 * 1024,
        'name': 'WebP Image',
    },
}
