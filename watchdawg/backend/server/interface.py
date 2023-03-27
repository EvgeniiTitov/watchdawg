import abc


class BaseServer(abc.ABC):
    @abc.abstractmethod
    def start_server(self) -> None:
        ...

    @abc.abstractmethod
    def stop_server(self) -> None:
        ...
