import abc
from typing import Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import socket


class BaseServer(abc.ABC):
    @abc.abstractmethod
    def start_server(self) -> None:
        ...


@dataclass()
class ConnectedClient:
    connection: socket.socket
    connected_at: datetime
    address: Tuple[str, int]
    client_name: Optional[str] = None
