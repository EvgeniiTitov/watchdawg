import numpy as np
import cv2

from watchdawg.preprocessor import BaseFramePreprocessor


class Resizer(BaseFramePreprocessor):

    def __init__(self, new_width: int) -> None:
        self._width = new_width

    def __call__(self, frame: np.ndarray, **kwargs) -> np.ndarray:
        curr_height, curr_width = frame.shape[:2]

        ratio = self._width / float(curr_width)
        dim = (self._width, int(curr_height * ratio))
        return cv2.resize(frame, dim, interpolate=cv2.INTER_AREA)

    def __repr__(self) -> str:
        return "Resizer"
