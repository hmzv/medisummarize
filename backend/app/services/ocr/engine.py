"""OCR helpers. Uncertain output stays uncertain; no medication/date autocorrect."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageFilter, ImageOps

from app.core.errors import AppError


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Limited preprocessing: grayscale, contrast stretch, light denoise."""
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray)
    return gray.filter(ImageFilter.MedianFilter(size=3))


def ocr_image(image: Image.Image) -> tuple[str, float | None, list[str]]:
    try:
        import pytesseract
    except ImportError as exc:
        raise AppError(status_code=500, detail="OCR is not available on this server.") from exc

    prepared = preprocess_for_ocr(image)
    warnings: list[str] = ["OCR output may contain recognition errors."]
    try:
        text = pytesseract.image_to_string(prepared)
        confidence = _mean_confidence(prepared)
    except pytesseract.TesseractNotFoundError as exc:
        raise AppError(
            status_code=500,
            detail="Tesseract OCR is not installed or not on PATH.",
        ) from exc
    except Exception:
        raise AppError(status_code=400, detail="OCR failed for this image.") from None
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    if not cleaned.strip():
        warnings.append("OCR produced no readable text.")
        return "", None, warnings
    if confidence is not None and confidence < 60:
        warnings.append("OCR confidence is low; verify numbers, dates, and medication names.")
    return cleaned, confidence, warnings


def ocr_png_bytes(png_bytes: bytes) -> tuple[str, float | None, list[str]]:
    with Image.open(BytesIO(png_bytes)) as image:
        rgb = image.convert("RGB")
        return ocr_image(rgb)


def _mean_confidence(image: Image.Image) -> float | None:
    try:
        import pytesseract

        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(value) for value in data.get("conf", []) if str(value).lstrip("-").isdigit() and int(value) >= 0]
        if not confidences:
            return None
        return sum(confidences) / len(confidences)
    except Exception:
        return None
