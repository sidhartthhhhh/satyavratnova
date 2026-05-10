import os
import uuid

from django.conf import settings


ALLOWED_EXTENSIONS = {
    ".mp4": "video/mp4",
    ".m3u8": "application/vnd.apple.mpegurl",
}


def validate_media_file(file_name, file_size):
    errors = []

    if not file_name:
        errors.append("file_name is required")
    else:
        ext = os.path.splitext(file_name.lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            errors.append("only .mp4 and .m3u8 files are allowed")

    try:
        size = int(file_size)
    except Exception:
        size = 0

    if size <= 0:
        errors.append("file_size must be bigger than zero")
    if size > settings.MAX_UPLOAD_BYTES:
        errors.append("file is too big")

    if errors:
        return {
            "ok": False,
            "errors": errors,
            "content_type": None,
            "size": size,
            "s3_key": None,
        }

    ext = os.path.splitext(file_name.lower())[1]
    return {
        "ok": True,
        "errors": [],
        "content_type": ALLOWED_EXTENSIONS[ext],
        "size": size,
        "s3_key": "uploads/" + str(uuid.uuid4()) + ext,
    }
