import abc

import numpy as np


class BaseFramePreprocessor(abc.ABC):

    @abc.abstractmethod
    def __call__(self, frame: np.ndarray, **kwargs) -> np.ndarray:
        ...

    @abc.abstractmethod
    def __repr__(self) -> str:
        ...
