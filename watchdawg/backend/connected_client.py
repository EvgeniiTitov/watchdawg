from typing import Optional, Tuple
from datetime import datetime
import uuid
from dataclasses import dataclass
import socket


@dataclass
class ConnectedClient:
    client_id: uuid.UUID
    connection: socket.socket
    connected_at: datetime
    address: Tuple[str, int]
    client_name: Optional[str] = None
