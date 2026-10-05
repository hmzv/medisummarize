"""Content-based file type detection. Client MIME types and names are untrusted."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import AppError
from app.models.document import FileKind

ALLOWED_EXTENSIONS = {
    ".pdf": FileKind.pdf,
    ".png": FileKind.image,
    ".jpg": FileKind.image,
    ".jpeg": FileKind.image,
    ".txt": FileKind.text,
}

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "txt": "text/plain; charset=utf-8",
}


@dataclass(frozen=True)
class DetectedFile:
    kind: FileKind
    subtype: str
    media_type: str
    stored_suffix: str
    page_count: int | None = None
    image_width: int | None = None
    image_height: int | None = None


def display_filename(raw_name: str | None) -> str:
    name = Path(raw_name or "upload").name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise AppError(status_code=400, detail="Invalid filename.")
    if ".." in name:
        raise AppError(status_code=400, detail="Invalid filename.")
    return name[:255]


def declared_extension(display_name: str) -> str:
    return Path(display_name).suffix.lower()


def sniff_header(header: bytes) -> str | None:
    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    return None


def validate_saved_file(path: Path, display_name: str, size_bytes: int, settings: Settings) -> DetectedFile:
    if size_bytes <= 0:
        raise AppError(status_code=400, detail="Empty files are not accepted.")
    if size_bytes > settings.max_upload_bytes:
        raise AppError(status_code=413, detail="File is too large.")

    ext = declared_extension(display_name)
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            status_code=415,
            detail="Unsupported file type. Upload a PDF, PNG, JPEG, or UTF-8 text file.",
        )

    header = path.read_bytes()[:16]
    sniffed = sniff_header(header)
    declared_kind = ALLOWED_EXTENSIONS[ext]

    if declared_kind is FileKind.pdf:
        if sniffed != "pdf":
            raise AppError(status_code=415, detail="File content does not match a PDF.")
        return _validate_pdf(path, settings)
    if declared_kind is FileKind.image:
        expected = "png" if ext == ".png" else "jpeg"
        if sniffed != expected:
            raise AppError(status_code=415, detail="File content does not match the image type.")
        return _validate_image(path, expected, settings)
    return _validate_text(path, sniffed, size_bytes, settings)


def _validate_pdf(path: Path, settings: Settings) -> DetectedFile:
    try:
        import fitz
    except ImportError as exc:
        raise AppError(status_code=500, detail="PDF parser is not available.") from exc
    try:
        with fitz.open(path) as pdf:
            if pdf.is_encrypted:
                raise AppError(status_code=400, detail="Encrypted PDFs are not accepted.")
            page_count = pdf.page_count
            if page_count <= 0:
                raise AppError(status_code=400, detail="The PDF has no pages.")
            if page_count > settings.max_pdf_pages:
                raise AppError(status_code=400, detail="The PDF has too many pages.")
    except AppError:
        raise
    except Exception:
        raise AppError(status_code=400, detail="The PDF could not be parsed.") from None
    return DetectedFile(
        kind=FileKind.pdf,
        subtype="pdf",
        media_type=MEDIA_TYPES["pdf"],
        stored_suffix=".pdf",
        page_count=page_count,
    )


def _validate_image(path: Path, subtype: str, settings: Settings) -> DetectedFile:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError):
        raise AppError(status_code=400, detail="The image could not be parsed.") from None
    if width < 16 or height < 16:
        raise AppError(status_code=400, detail="The image is too small.")
    if width > settings.max_image_side or height > settings.max_image_side:
        raise AppError(status_code=400, detail="The image dimensions are too large.")
    if width * height > settings.max_image_pixels:
        raise AppError(status_code=400, detail="The image has too many pixels.")
    return DetectedFile(
        kind=FileKind.image,
        subtype=subtype,
        media_type=MEDIA_TYPES[subtype],
        stored_suffix=".png" if subtype == "png" else ".jpg",
        image_width=width,
        image_height=height,
    )


def _validate_text(path: Path, sniffed: str | None, size_bytes: int, settings: Settings) -> DetectedFile:
    if sniffed in {"pdf", "png", "jpeg"}:
        raise AppError(status_code=415, detail="File content does not match a text file.")
    if size_bytes > settings.max_text_bytes:
        raise AppError(status_code=413, detail="Text file is too large.")
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise AppError(status_code=415, detail="Binary files are not accepted as text.")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        raise AppError(status_code=415, detail="Text files must be valid UTF-8.") from None
    return DetectedFile(
        kind=FileKind.text,
        subtype="txt",
        media_type=MEDIA_TYPES["txt"],
        stored_suffix=".txt",
    )
