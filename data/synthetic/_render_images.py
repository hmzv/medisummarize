"""Render synthetic OCR images. SYNTHETIC — NOT A REAL PATIENT."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ):
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _draw_lines(
    path: Path,
    lines: list[str],
    *,
    size: tuple[int, int],
    bg: str,
    fill: str,
    font_size: int,
    degrade: bool = False,
) -> None:
    image = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(image)
    font = _font(font_size)
    y = 36
    for line in lines:
        draw.text((36, y), line, fill=fill, font=font)
        y += font_size + 18
    if degrade:
        image = image.filter(ImageFilter.GaussianBlur(radius=1.2))
        image = ImageEnhance.Contrast(image).enhance(0.55)
        image = ImageEnhance.Brightness(image).enhance(1.15)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")


def main() -> None:
    _draw_lines(
        ROOT / "case_b_ocr" / "scan.png",
        [
            "SYNTHETIC — NOT A REAL PATIENT",
            "Vital-sign image note (fictional)",
            "Blood pressure 128/82 mmHg",
            "Temperature 36.8 C",
        ],
        size=(1100, 420),
        bg="white",
        fill="black",
        font_size=36,
    )
    _draw_lines(
        ROOT / "case_f_poor_ocr" / "noisy_scan.png",
        [
            "SYNTHETIC — NOT A REAL PATIENT",
            "Laboratory image note (fictional)",
            "HbA1c 7.8 %",
        ],
        size=(900, 280),
        bg="#d8d8d8",
        fill="#6a6a6a",
        font_size=28,
        degrade=True,
    )
    print("wrote OCR demonstration PNGs")


if __name__ == "__main__":
    main()
