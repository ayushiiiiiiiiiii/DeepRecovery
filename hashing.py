import hashlib
from pathlib import Path
from typing import Union

def sha256_file(path: Union[str, Path], chunk_size: int = 4096) -> str:
    """
    Compute SHA-256 hash of a file, reading in chunks.
    Returns lowercase hex digest string.
    """
    path = Path(path)
    h = hashlib.sha256()  # SHA-256 from hashlib stdlib
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file_integrity(path: Union[str, Path], expected_sha256: str) -> bool:
    """
    Compare file's SHA-256 with expected hash (string).
    Returns True if match, False otherwise.
    """
    actual = sha256_file(path)
    # normalize case
    return actual.lower() == expected_sha256.strip().lower()


if __name__ == "__main__":
    # 1) Generate hash for a sample image/doc
    sample_path = "sample_image_or_doc.bin"  # replace with your real file
    print(f"Computing SHA-256 for: {sample_path}")
    digest = sha256_file(sample_path)
    print(f"SHA-256: {digest}")

    # 2) Integrity verification example
    expected = digest  # in a real case, this would come from a trusted source
    ok = verify_file_integrity(sample_path, expected)
    if ok:
        print("Integrity OK: file matches expected SHA-256.")
    else:
        print("Integrity FAILED: file has been modified or corrupted.")
