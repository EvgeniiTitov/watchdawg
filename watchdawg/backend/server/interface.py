import abc


class BaseServer(abc.ABC):
    @abc.abstractmethod
    def start_server(self) -> None:
        ...

    @abc.abstractmethod
    def stop_server(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def total_connected_clients(self) -> int:
        ...
