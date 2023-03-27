import abc
import uuid
from typing import List

import numpy as np

from watchdawg.backend.messages import ConnectedClient


class BaseResultsWriter(abc.ABC):
    @abc.abstractmethod
    def register_client(self, client: ConnectedClient) -> None:
        """When a new client gets registered, ResultWriter create a new cv2
        window / creates a new file to write feed to depending on the selected
        mode
        """
        ...

    @abc.abstractmethod
    def unregister_client(self, client_id: uuid.UUID):
        """Client disconnected, close file / kill CV2 window showing the feed
        for this client
        """
        ...

    @abc.abstractmethod
    def process_batch(self, frames: List[np.ndarray], detections) -> None:
        """Processes a batch of frames with results / detections"""
        ...
