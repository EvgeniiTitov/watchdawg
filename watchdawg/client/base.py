import abc
from typing import Optional

import numpy as np
import cv2

from watchdawg.source import BaseSource
from watchdawg.preprocessor import BaseFramePreprocessor


class BaseClient(abc.ABC):
    def __init__(
        self,
        name: str,
        video_source: BaseSource,
        preprocessor: Optional[BaseFramePreprocessor] = None,
        every_nth_frame: int = 0
    ) -> None:
        self._name = name
        self._video_source = video_source
        self._preprocessor = preprocessor
        self._every_nth_frame = every_nth_frame

    @staticmethod
    def show_frame(frame: np.ndarray, window_name: str = "") -> None:
        cv2.imshow(window_name, frame)
        cv2.waitKey(1)

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    def start_client(self) -> None:
        ...
