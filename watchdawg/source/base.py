import abc

import numpy as np


class BaseSource(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @abc.abstractmethod
    def __iter__(self) -> np.ndarray:
        ...
