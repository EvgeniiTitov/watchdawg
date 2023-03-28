from typing import Optional, Tuple
from datetime import datetime
import uuid
from dataclasses import dataclass
import socket

import numpy as np


class FeedProcessorMessage:
    pass


@dataclass
class ClientDisconnectedMessage(FeedProcessorMessage):
    client_id: uuid.UUID


@dataclass
class ProcessFrameMessage(FeedProcessorMessage):
    client_id: uuid.UUID
    frame: np.ndarray
    detections: Optional[dict] = None


@dataclass
class ConnectedClient:
    client_id: uuid.UUID
    connection: socket.socket
    connected_at: datetime
    address: Tuple[str, int]
    client_name: Optional[str] = None
