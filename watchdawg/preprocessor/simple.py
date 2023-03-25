import numpy as np
import cv2

from watchdawg.preprocessor import BaseFramePreprocessor


class SimplePreprocessor(BaseFramePreprocessor):
    def __init__(self, new_width: int, flip: bool) -> None:
        self._width = new_width
        self._flip = flip

    def __call__(self, frame: np.ndarray, **kwargs) -> np.ndarray:
        curr_height, curr_width = frame.shape[:2]
        ratio = self._width / float(curr_width)
        dim = (self._width, int(curr_height * ratio))
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        if self._flip:
            frame = cv2.flip(frame, 180)
        return frame

    def __repr__(self) -> str:
        return "Resizer"
