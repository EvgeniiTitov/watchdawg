import numpy as np
import cv2

from watchdawg.client.preprocessor import BaseFramePreprocessor


class Resizer(BaseFramePreprocessor):
    def __init__(self, new_width: int, new_height: int, flip: bool) -> None:
        self._new_width = new_width
        self._new_height = new_height
        self._flip = flip

    def __call__(self, frame: np.ndarray, **kwargs) -> np.ndarray:
        frame = cv2.resize(
            frame,
            (self._new_width, self._new_height),
            interpolation=cv2.INTER_AREA
        )
        if self._flip:
            frame = cv2.flip(frame, 180)
        return frame

    def __repr__(self) -> str:
        return "Resizer"
