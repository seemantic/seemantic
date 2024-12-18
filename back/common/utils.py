from io import BytesIO

from xxhash import xxh3_128_hexdigest


def hash_file_content(content: BytesIO) -> str:
    content.seek(0)
    bytes_content = content.read()
    raw_hash = xxh3_128_hexdigest(bytes_content)
    return raw_hash
