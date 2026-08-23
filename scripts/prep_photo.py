#!/usr/bin/env python3
"""
prep_photo.py
Downloads the GitHub avatar (or accepts a local file), removes the background,
boosts local contrast with CLAHE, and composites onto pure white.
Output: source-prepped.png

Usage:
    python scripts/prep_photo.py                  # downloads GitHub avatar
    python scripts/prep_photo.py path/to/photo.jpg  # uses local file
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove
import requests
from io import BytesIO

AVATAR_URL = "https://avatars.githubusercontent.com/u/232060506?v=4"
OUT_FILE = Path(__file__).resolve().parent.parent / "source-prepped.png"


def load_source(path: str | None = None) -> Image.Image:
    """Load the source photo — from disk or download the GitHub avatar."""
    if path and Path(path).exists():
        print(f"Loading local file: {path}")
        return Image.open(path).convert("RGBA")
    else:
        print(f"Downloading avatar from {AVATAR_URL}...")
        resp = requests.get(AVATAR_URL, timeout=30)
        resp.raise_for_status()
        return Image.open(BytesIO(resp.content)).convert("RGBA")


def remove_background(img: Image.Image) -> Image.Image:
    """Strip background using rembg, returning RGBA with transparent bg."""
    print("Removing background...")
    return remove(img)


def boost_contrast_clahe(img: Image.Image) -> Image.Image:
    """
    Convert to grayscale, apply CLAHE (contrast-limited adaptive histogram
    equalization) to bring out highlights and shadows in flat-lit faces.
    """
    print("Boosting contrast with CLAHE...")
    arr = np.array(img)

    # If RGBA, extract the alpha channel for later compositing
    has_alpha = arr.shape[2] == 4 if len(arr.shape) == 3 else False
    if has_alpha:
        alpha = arr[:, :, 3]
        rgb = arr[:, :, :3]
    else:
        alpha = None
        rgb = arr

    # Convert to grayscale
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Rebuild as RGBA with original alpha
    if alpha is not None:
        result = np.stack([enhanced, enhanced, enhanced, alpha], axis=-1)
    else:
        result = np.stack([enhanced, enhanced, enhanced], axis=-1)

    return Image.fromarray(result)


def composite_on_white(img: Image.Image) -> Image.Image:
    """Paste the RGBA image onto a pure white background → grayscale PNG."""
    print("Compositing onto white background...")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
    return white.convert("L")  # final grayscale


def main():
    source_path = sys.argv[1] if len(sys.argv) > 1 else None

    img = load_source(source_path)
    img = remove_background(img)
    img = boost_contrast_clahe(img)
    img = composite_on_white(img)

    img.save(OUT_FILE)
    print(f"Saved -> {OUT_FILE}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
