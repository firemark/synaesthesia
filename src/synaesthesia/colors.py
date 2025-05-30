import cv2 as cv
import numpy as np
import skimage as ski
import skimage.morphology as mor
from dataclasses import dataclass, replace


@dataclass
class Mask:
    index: int
    color: np.ndarray
    mask: np.ndarray


def get_colors(frame) -> dict[str, Mask]:
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV_FULL) / 255.0

    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    colors = {
        "red": Mask(1, np.array((0, 0, 255)), (v > 0.3) & (s > 0.3) & ((h < 0.1) | (h > 0.9))),
        "green": Mask(2, np.array((0, 255, 0)), (v > 0.3) & (s > 0.3) & ((h > 0.2) & (h < 0.4))),
        "blue": Mask(3, np.array((255, 0, 0)), (v > 0.3) & (s > 0.3) & ((h > 0.5) & (h < 0.7))),
    }

    return {
        color: replace(mask, mask=_morphology(mask.mask))
        for color, mask in colors.items()
    }


def _morphology(mask):
    mask = mor.erosion(mask, ski.morphology.disk(2))
    mask = mor.dilation(mask, ski.morphology.disk(3))
    mask = mor.closing(mask, ski.morphology.disk(2))
    return mask
