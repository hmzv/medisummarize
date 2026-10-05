"""Protected local storage for original uploads. Paths are never taken from the client."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import AppError
from app.models.document import Document


def record_dir(settings: Settings, owner_id: uuid.UUID, record_id: uuid.UUID) -> Path:
    base = settings.resolved_storage_dir
    path = (base / str(owner_id) / str(record_id)).resolve()
    if not path.is_relative_to(base):
        raise AppError(status_code=500, detail="Storage path could not be resolved.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def document_path(settings: Settings, document: Document) -> Path:
    base = settings.resolved_storage_dir
    path = (base / str(document.owner_id) / str(document.record_id) / document.stored_name).resolve()
    if not path.is_relative_to(base):
        raise AppError(status_code=500, detail="Storage path could not be resolved.")
    return path


def write_upload_to_temp(upload: UploadFile, destination: Path, max_bytes: int) -> tuple[int, str]:
    hasher = hashlib.sha256()
    size = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise AppError(status_code=413, detail="File is too large.")
                hasher.update(chunk)
                handle.write(chunk)
    except AppError:
        destination.unlink(missing_ok=True)
        raise
    return size, hasher.hexdigest()


def delete_quiet(path: Path) -> None:
    path.unlink(missing_ok=True)
