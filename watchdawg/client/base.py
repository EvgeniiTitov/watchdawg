import abc

from source.base import BaseSource


class BaseClient(abc.ABC):
    def __init__(self, name: str, source: BaseSource) -> None:
        self._name = name
        self._source = source

    @property
    def name(self) -> str:
        return self._name

    @abc.abstractmethod
    @property
    def address(self) -> str:
        ...

    @abc.abstractmethod
    def start_client(self) -> None:
        ...
