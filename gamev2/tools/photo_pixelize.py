#!/usr/bin/env python3
"""photo_pixelize.py — render a photo as crisp 160×144 pixel art.

Ported from the imgscaling study's winning renderer (runner.py ->
crisp_pixelize, colours=16, edge_strength=0.12): saliency-guided crop to
10:9, direct INTER_AREA reduction (no pre-blur), luminance sharpen, LAB
k-means palette from the photo's own colours, sparse structural outlines
moved to darker palette colours, and face-aware speck cleanup. Blog-post
photos go through this before hanging in the dialogue photo frame.

Needs numpy + Pillow + opencv-contrib (cv2.saliency); see
tools/requirements-photos.txt.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

TARGET = (160, 144)

# Prevent unexpectedly huge decoded images.
Image.MAX_IMAGE_PIXELS = 40_000_000


def load_rgb(path: Path, background=(245, 245, 245)) -> np.ndarray:
    """Load an image, correct its orientation, and flatten transparency."""
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        image.load()

        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            canvas = Image.new("RGBA", rgba.size, (*background, 255))
            image = Image.alpha_composite(canvas, rgba).convert("RGB")
        else:
            image = image.convert("RGB")

        return np.asarray(image)


def find_saliency_point(rgb: np.ndarray) -> tuple[float, float]:
    """Return a weighted centre for the visually prominent image content."""
    height, width = rgb.shape[:2]

    detector = cv2.saliency.StaticSaliencySpectralResidual_create()
    success, saliency = detector.computeSaliency(
        cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    )

    if not success:
        return width / 2, height / 2

    saliency = cv2.resize(
        saliency,
        (width, height),
        interpolation=cv2.INTER_LINEAR,
    )

    sigma = max(width, height) / 40
    saliency = cv2.GaussianBlur(
        saliency,
        (0, 0),
        sigmaX=sigma,
        sigmaY=sigma,
    )

    # Ignore low-level texture and retain the more prominent regions.
    floor = np.percentile(saliency, 65)
    weights = np.maximum(saliency - floor, 0)
    total = float(weights.sum())

    if total < 1e-6:
        return width / 2, height / 2

    ys, xs = np.indices(weights.shape)
    cx = float((xs * weights).sum() / total)
    cy = float((ys * weights).sum() / total)

    # A centre bias prevents unstable crops when saliency falls on an edge.
    cx = 0.8 * cx + 0.2 * width / 2
    cy = 0.8 * cy + 0.2 * height / 2

    return cx, cy


def crop_to_target_ratio(rgb: np.ndarray) -> np.ndarray:
    """Crop around the salient point using the final 10:9 aspect ratio."""
    height, width = rgb.shape[:2]
    target_ratio = TARGET[0] / TARGET[1]

    if width / height > target_ratio:
        crop_height = height
        crop_width = round(height * target_ratio)
    else:
        crop_width = width
        crop_height = round(width / target_ratio)

    cx, cy = find_saliency_point(rgb)

    x0 = int(
        np.clip(
            round(cx - crop_width / 2),
            0,
            width - crop_width,
        )
    )
    y0 = int(
        np.clip(
            round(cy - crop_height / 2),
            0,
            height - crop_height,
        )
    )

    return rgb[
        y0 : y0 + crop_height,
        x0 : x0 + crop_width,
    ]


def sharpen_luminance(rgb: np.ndarray, amount: float = 0.42) -> np.ndarray:
    """Sharpen existing geometry without smoothing or inventing new shapes."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    luminance = lab[:, :, 0]
    soft = cv2.GaussianBlur(luminance, (0, 0), sigmaX=0.75)
    sharp = cv2.addWeighted(luminance, 1.0 + amount, soft, -amount, 0)
    lab[:, :, 0] = sharp
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def quantize_lab(rgb: np.ndarray, colours: int) -> tuple[np.ndarray, np.ndarray]:
    """Reduce colour while retaining the source image's own palette."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    samples = lab.reshape(-1, 3).astype(np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
        40,
        0.3,
    )
    cv2.setRNGSeed(0)
    _, labels, centres = cv2.kmeans(
        samples,
        colours,
        None,
        criteria,
        5,
        cv2.KMEANS_PP_CENTERS,
    )
    palette_lab = np.clip(np.rint(centres), 0, 255).astype(np.uint8)
    palette_rgb = cv2.cvtColor(
        palette_lab.reshape(1, -1, 3),
        cv2.COLOR_LAB2RGB,
    ).reshape(-1, 3)
    indexed = labels.reshape(lab.shape[:2])
    return palette_rgb[indexed], palette_rgb


def structural_edges(rgb: np.ndarray) -> np.ndarray:
    """Return sparse one-pixel edges while rejecting dense photographic texture."""
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    low = int(np.percentile(gray, 35))
    high = int(np.percentile(gray, 72))
    edges = cv2.Canny(gray, max(25, low), max(60, high), L2gradient=True)

    count, labels, stats, _ = cv2.connectedComponentsWithStats(edges, connectivity=8)
    cleaned = np.zeros_like(edges)
    for label in range(1, count):
        area = stats[label, cv2.CC_STAT_AREA]
        width = stats[label, cv2.CC_STAT_WIDTH]
        height = stats[label, cv2.CC_STAT_HEIGHT]
        if area >= 5 and max(width, height) >= 4:
            cleaned[labels == label] = 255

    # A busy local patch is texture, not an outline. This especially prevents
    # foliage and tabletop clutter from overwhelming the actual silhouettes.
    density = cv2.blur((cleaned > 0).astype(np.float32), (7, 7))
    cleaned[density > 0.30] = 0
    return cleaned > 0


def face_mask_for_crop(rgb: np.ndarray) -> np.ndarray:
    """Mark face pixels so cleanup cannot erase eyes or facial highlights."""
    working = cv2.resize(rgb, (640, 576), interpolation=cv2.INTER_AREA)
    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = detector.detectMultiScale(
        cv2.cvtColor(working, cv2.COLOR_RGB2GRAY),
        scaleFactor=1.08,
        minNeighbors=4,
        minSize=(20, 20),
    )
    mask = np.zeros((TARGET[1], TARGET[0]), dtype=np.uint8)
    for x, y, width, height in faces:
        centre = (round((x + width / 2) / 4), round((y + height / 2) / 4))
        axes = (max(3, round(width / 4 * 0.65)), max(3, round(height / 4 * 0.75)))
        cv2.ellipse(mask, centre, axes, 0, 0, 360, 255, -1)
    return mask > 0


def remove_single_pixel_specks(rgb: np.ndarray, protected: np.ndarray) -> np.ndarray:
    """Remove isolated palette pixels while retaining lines and small features."""
    result = rgb.copy()
    height, width = result.shape[:2]
    for _ in range(2):
        source = result.copy()
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if protected[y, x]:
                    continue
                neighbours = source[y - 1 : y + 2, x - 1 : x + 2].reshape(-1, 3)
                neighbours = np.delete(neighbours, 4, axis=0)
                values, counts = np.unique(neighbours, axis=0, return_counts=True)
                winner = int(counts.argmax())
                if counts[winner] >= 5 and not np.array_equal(source[y, x], values[winner]):
                    result[y, x] = values[winner]
    return result


def apply_palette_outlines(
    quantized: np.ndarray,
    palette: np.ndarray,
    edge_mask: np.ndarray,
    strength: float,
) -> np.ndarray:
    """Move edge pixels to a darker related palette colour, never soft black."""
    if strength <= 0:
        return quantized

    result = quantized.copy()
    palette_lab = cv2.cvtColor(
        palette.reshape(1, -1, 3),
        cv2.COLOR_RGB2LAB,
    ).reshape(-1, 3).astype(np.float32)
    image_lab = cv2.cvtColor(quantized, cv2.COLOR_RGB2LAB).astype(np.float32)
    minimum_drop = 6 + strength * 34

    ys, xs = np.nonzero(edge_mask)
    for y, x in zip(ys, xs):
        current = image_lab[y, x]
        darker = palette_lab[:, 0] <= current[0] - minimum_drop
        if not np.any(darker):
            continue
        # Prefer matching hue/chroma, then the nearest useful darker value.
        chroma = ((palette_lab[:, 1:] - current[1:]) ** 2).sum(axis=1)
        luminance = (palette_lab[:, 0] - (current[0] - minimum_drop)) ** 2
        score = chroma * 1.7 + luminance * 0.35
        score[~darker] = np.inf
        result[y, x] = palette[int(score.argmin())]
    return result


def crisp_pixelize(
    source: Path,
    destination: Path,
    colours: int = 16,
    edge_strength: float = 0.12,
) -> None:
    rgb = crop_to_target_ratio(load_rgb(source))
    protected = face_mask_for_crop(rgb)

    # Direct area reduction keeps faces, limbs, rooflines and table objects in
    # their original positions. There is deliberately no pre-blur here.
    small = cv2.resize(rgb, TARGET, interpolation=cv2.INTER_AREA)
    sharp = sharpen_luminance(small)
    quantized, palette = quantize_lab(sharp, colours)
    edges = structural_edges(sharp)
    final = apply_palette_outlines(quantized, palette, edges, edge_strength)
    final = remove_single_pixel_specks(final, protected)

    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(final).save(destination, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render crisp, structure-preserving pixel art.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--colours", type=int, default=16)
    parser.add_argument("--edge-strength", type=float, default=0.12)
    args = parser.parse_args()
    if not 8 <= args.colours <= 64:
        parser.error("--colours must be between 8 and 64")
    if not 0 <= args.edge_strength <= 1:
        parser.error("--edge-strength must be between 0 and 1")
    crisp_pixelize(args.source, args.destination, args.colours, args.edge_strength)


if __name__ == "__main__":
    main()
