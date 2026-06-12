import os
import uuid
import aiofiles
from fastapi import UploadFile

UPLOAD_DIR = "uploads"

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "video/mp4": "video",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/vnd.ms-excel": "excel",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

async def save_file(file: UploadFile) -> dict:
    # Validate mime type
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError(f"File type {file.content_type} not allowed")

    # Read file content
    content = await file.read()

    # Validate size
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds 50MB limit")

    # Generate unique stored name
    extension = file.filename.split(".")[-1]
    stored_name = f"{uuid.uuid4()}.{extension}"
    storage_path = os.path.join(UPLOAD_DIR, stored_name)

    # Save to disk
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    return {
        "original_name": file.filename,
        "stored_name": stored_name,
        "storage_path": storage_path,
        "mime_type": file.content_type,
        "file_type": ALLOWED_TYPES[file.content_type],
        "size_bytes": str(len(content)),
    }