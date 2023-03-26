import abc
import uuid
from typing import Tuple

import numpy as np


class BaseProcessor(abc.ABC):
    @abc.abstractmethod
    def register_client(
        self, client_name: str, client_address: Tuple[str, int]
    ) -> uuid.UUID:
        """Registers a new client with the Processor. The processor will
        generate a new uuid for the client, create new GUI window / create
        folder to write client's feed to, etc
        """
        ...

    @abc.abstractmethod
    def unregister_client(self, client_id: uuid.UUID):
        """Puts a stop message into the client's internal queue indicating
        there will be no more frames from that client as its socket is closed
        """
        ...

    @abc.abstractmethod
    def submit_frame_for_processing(
        self, client_id: uuid.UUID, frame: np.ndarray
    ) -> None:
        """Puts a client frame into its internal queue for processing"""
        ...
