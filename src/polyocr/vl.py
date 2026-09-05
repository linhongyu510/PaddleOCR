"""Security boundary shared by the optional PaddleOCR-VL deployment."""

import base64
import binascii

from polyocr.api.errors import ServiceError


def decode_vl_input(value: str, *, max_bytes: int) -> bytes:
    lowered = value.lstrip().casefold()
    if lowered.startswith(("http://", "https://")):
        raise ServiceError(
            "url_input_forbidden",
            "Remote URL input is not accepted; upload the file content.",
            422,
        )
    if len(value) > ((max_bytes + 2) // 3) * 4 + 4:
        raise ServiceError("file_too_large", "Uploaded file exceeds the byte limit.", 413)
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ServiceError("invalid_file", "File is not valid base64.", 422) from exc
    if len(data) > max_bytes:
        raise ServiceError("file_too_large", "Uploaded file exceeds the byte limit.", 413)
    if not data:
        raise ServiceError("invalid_file", "Uploaded file is empty.", 422)
    return data
