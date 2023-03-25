import abc
from typing import Optional

from watchdawg.source import BaseSource
from watchdawg.preprocessor import BaseFramePreprocessor


class BaseClient(abc.ABC):
    def __init__(
        self, name: str,
        video_source: BaseSource,
        preprocessor: Optional[BaseFramePreprocessor] = None
    ) -> None:
        self._name = name
        self._video_source = video_source
        self._preprocessor = preprocessor

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    def start_client(self) -> None:
        ...
