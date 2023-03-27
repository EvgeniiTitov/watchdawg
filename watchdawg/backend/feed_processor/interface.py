import abc
import uuid
from typing import Optional

import numpy as np

from watchdawg.backend.messages import ConnectedClient


class BaseFeedProcessor(abc.ABC):
    @abc.abstractmethod
    def register_client(self, client: ConnectedClient) -> None:
        """Registers a new client (connection accepted by the TCPServer) with
        the FeedProcessor
        """
        ...

    @abc.abstractmethod
    def unregister_client(self, client_id: uuid.UUID) -> None:
        """Puts a stop message with the client id signalling to the
        FeedProcessor there will be no more frames for that client
        """
        ...

    @abc.abstractmethod
    def enqueue_frame_for_processing(
        self, client_id: uuid.UUID, frame: np.ndarray
    ) -> None:
        """Submits the frame for processing"""
        ...

    @abc.abstractmethod
    def stop(self, timeout: Optional[float]) -> None:
        """Signals FeedProcessor to stop"""
        ...
