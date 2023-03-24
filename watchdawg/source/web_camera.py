import cv2
import numpy as np

from source.base import BaseSource


class WebCamera(BaseSource):
    def __init__(self) -> None:
        self._cap = cv2.VideoCapture(0)

    def __iter__(self) -> np.ndarray:
        while True:
            has_frame, frame = self._cap.read()
            if not has_frame:
                break
            yield frame

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.close()
        except Exception:
            pass

    def close(self) -> None:
        if self._cap.isOpened():
            self._cap.release()
