import cv2 as cv
import numpy as np
import skimage as ski
import skimage.morphology as mor
from dataclasses import dataclass, replace

RANGE = 0.2

@dataclass
class MaskConfig:
    index: int
    color: np.ndarray
    h: float
    v: float = 0.3
    s: float = 0.3


@dataclass
class Mask:
    config: MaskConfig
    mask: np.ndarray


def get_colors(frame, config: dict[str, MaskConfig]) -> dict[str, Mask]:
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV_FULL) / 255.0

    return {
        color: _config_to_mask(hsv, mask_config)
        for color, mask_config in config.items()
    }


def _config_to_mask(hsv, config: MaskConfig) -> Mask:
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    mask = v > config.v
    mask &= s > config.s
    next_h = config.h + RANGE
    if next_h > 1.0:
        mask &= (h > config.h) | (h < np.fmod(next_h, 1.0))
    else:
        mask &= (h > config.h) & (h < next_h)

    return Mask(
        config=config,
        mask=_morphology(mask),
    )


def _morphology(mask):
    mask = mor.erosion(mask, ski.morphology.disk(2))
    mask = mor.dilation(mask, ski.morphology.disk(3))
    mask = mor.closing(mask, ski.morphology.disk(2))
    return mask
