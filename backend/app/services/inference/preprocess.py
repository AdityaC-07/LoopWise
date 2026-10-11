"""Reference-matching image preprocessing for the ONNX waste classifier.

This is a dependency-light (Pillow + numpy only) implementation of the exact
transform that the verified model was trained and evaluated with
(Ultralytics 8.4.175 / torchvision classification path):

    Resize(shortest edge = size, BILINEAR)
    CenterCrop(size)
    ToTensor  (HWC -> CHW, uint8 -> float32 in [0, 1], i.e. divide by 255)

There is **no** ImageNet mean/std normalisation: the reference model uses
mean = (0, 0, 0) and std = (1, 1, 1), i.e. a plain divide-by-255.

Why a separate module: the offline evaluator (``ml/evaluate.py --preprocess
backend``) imports *this exact file* to verify that the deployed backend
produces the same predictions as the reference pipeline. Keeping it free of
torch/torchvision/onnxruntime and of any `app.*` imports lets it be loaded
standalone (importlib) by the evaluator, so backend and evaluation cannot drift.

Geometry notes (matches torchvision.transforms.functional for PIL images):
  * Resize(224) on a ``w x h`` image sets the shorter edge to 224 and the
    longer edge to ``int(224 * longer / shorter)`` (integer truncation).
  * CenterCrop(224) uses ``left = int(round((w - 224) / 2))`` (banker's
    rounding, as Python's ``round``) and the same for ``top``.
  * PIL images are resized with ``Image.BILINEAR`` (torchvision delegates
    directly to ``PIL.Image.resize`` for the PIL backend).
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
from PIL import Image

DEFAULT_INPUT_SIZE = 224
NUM_CHANNELS = 3


def _resized_wh(w: int, h: int, size: int) -> Tuple[int, int]:
    """Return the (width, height) after matching the shorter edge to ``size``."""
    short, long = (w, h) if w <= h else (h, w)
    new_short = int(size)
    new_long = int(int(size) * long / short)
    if w <= h:
        return new_short, new_long
    return new_long, new_short


def _center_crop_box(w: int, h: int, size: int) -> Tuple[int, int, int, int]:
    """Return the (left, top, right, bottom) centre-crop box (torchvision rule)."""
    left = int(round((w - size) / 2.0))
    top = int(round((h - size) / 2.0))
    return left, top, left + size, top + size


def preprocess_image(image: Image.Image, size: int = DEFAULT_INPUT_SIZE) -> np.ndarray:
    """Return an NCHW float32 tensor in [0, 1] matching the reference transform.

    Args:
        image: a decoded PIL image (any mode; converted to RGB here).
        size: the square input edge length (the classifier uses 224).

    Returns:
        ``np.ndarray`` of shape ``[1, 3, size, size]``, dtype float32, range [0, 1].
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError(f"size must be a positive int, got {size!r}")

    img = image.convert("RGB")
    w, h = img.size
    new_w, new_h = _resized_wh(w, h, size)

    if (new_w, new_h) != (w, h):
        img = img.resize((new_w, new_h), Image.BILINEAR)

    if new_w < size or new_h < size:
        # Defensive: cannot happen when the longer edge >= the shorter edge,
        # but keep behaviour safe (pad, then crop) rather than crashing.
        canvas = Image.new("RGB", (max(new_w, size), max(new_h, size)), (0, 0, 0))
        canvas.paste(img, ((canvas.width - new_w) // 2, (canvas.height - new_h) // 2))
        img = canvas
        new_w, new_h = img.size

    img = img.crop(_center_crop_box(new_w, new_h, size))

    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(arr, (2, 0, 1))[np.newaxis, ...]
