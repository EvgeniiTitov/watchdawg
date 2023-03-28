from typing import Optional, List
import uuid
from dataclasses import dataclass

import numpy as np


class BusMessage:
    pass


@dataclass
class ClientDisconnectedMessage(BusMessage):
    client_id: uuid.UUID


@dataclass
class NewClientConnectedMessage(BusMessage):
    client_id: uuid.UUID


@dataclass
class ProcessFrameMessage(BusMessage):
    client_id: uuid.UUID
    frame: np.ndarray
    detections: Optional[dict] = None


@dataclass
class FramesBatchMessage(BusMessage):
    batch: List[ProcessFrameMessage]
