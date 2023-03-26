import uuid
from queue import Queue
from typing import MutableMapping, Tuple
import threading

import numpy as np

from watchdawg.util.logger import get_logger
from watchdawg.processor.base import BaseProcessor


logger = get_logger("processor")


class ClientDisconnectedMessage:
    pass


class ProcessorStoppedError(Exception):
    """This exception is raised if there is an attempt to register/submit
    a frame for processing with the stopping Processor"""


class Processor(BaseProcessor):

    def __init__(self, client_queue_size: int) -> None:
        # TODO: Gets model scorer
        # TODO: Gets a sink to forward processed frames to
        self._client_queue_size = client_queue_size

        self._lock = threading.Lock()
        self._clients: MutableMapping[uuid.UUID, Queue] = {}

        self._stop_event = threading.Event()
        self._run_thread = threading.Thread(target=self.run)
        self._run_thread.start()

    def register_client(
        self, client_name: str, client_address: Tuple[str, int]
    ) -> uuid.UUID:
        if self._stop_event.is_set():
            raise ProcessorStoppedError(
                "Cannot register new client, Processor is stopping"
            )

        client_id = uuid.uuid4()
        client_queue = Queue(maxsize=self._client_queue_size)
        with self._lock:
            self._clients[client_id] = client_queue
        logger.info(
            f"Registered new client {client_address} with the processor"
        )
        return client_id

    def unregister_client(self, client_id: uuid.UUID) -> None:
        if client_id not in self._clients:
            raise KeyError(f"Client with ID {client_id} is not registered")

        with self._lock:
            client_queue = self._clients.get(client_id)
        client_queue.put(ClientDisconnectedMessage())

    def submit_frame_for_processing(
        self, client_id: uuid.UUID, frame: np.ndarray
    ) -> None:
        # TODO: What if queue is full? + it holds old frames we don't care about
        #       and need to prioritise new ones
        #       If queue gets full, there is a congestion downstream, client
        #       won't slow down sending frames, so recreate the queue dropping
        #       old frames to accomodate the fresh ones?
        if self._stop_event.is_set():
            raise ProcessorStoppedError(
                f"Cannot process frame from client {client_id}. "
                f"Processor is stopping"
            )
        if client_id not in self._clients:
            raise KeyError(f"Client with ID {client_id} is not registered")

        with self._lock:
            client_queue = self._clients.get(client_id)
        client_queue.put(frame)

    def run(self) -> None:
        logger.debug("Processor started")
        # TODO: Runs in a dedicated thread
        #       1. Accumulates a batch of frames and passes it to the model scorer
        #       2. Receive results
        #       3. Pass to sink (results writer) to show/write to disk

        #       If there're no clients/queue - idle

        logger.debug("Processor stopped")

    def _collect_batch(self):
        # TODO: Could be limited by a batch size or time window
        #       If batch size < total connected clients, start collecting next
        #       batch from where you left off (not from the start of the queues)
        pass

    def stop(self, timeout: int = 10) -> None:
        self._stop_event.set()
        self._run_thread.join(timeout=timeout)
        if self._run_thread.is_alive():
            logger.error("Failed to stop Processor in reasonable time")
        else:
            logger.debug("Processor stopped gracefully")
