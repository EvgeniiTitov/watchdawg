import time
from typing import Set, Optional, List
import uuid
from queue import Queue, Empty
import threading

import numpy as np

from watchdawg.backend.feed_processor.interface import BaseFeedProcessor
from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import (
    ClientDisconnectedMessage,
    ProcessFrameMessage,
    ConnectedClient,
    FeedProcessorMessage,
)
from watchdawg.backend.exceptions import FeedProcessorStoppedError


logger = get_logger("feed_processor")


# TODO: Replace with an actual model
TODO_MODEL = lambda batch: ["Detections: {}" for item in batch]  # noqa


class FeedProcessor(BaseFeedProcessor):
    def __init__(
        self,
        internal_queue_size: int,
        batch_size: int,
        build_batch_time_window: float,
        result_queue: Queue,
        model=TODO_MODEL,
    ) -> None:
        self._task_queue: "Queue[FeedProcessorMessage]" = Queue(
            maxsize=internal_queue_size
        )
        self._batch_size = batch_size
        self._time_window = build_batch_time_window
        self._result_queue = result_queue
        self._model = model

        self._lock = threading.Lock()
        self._clients: Set[uuid.UUID] = set()

        self._stop_event = threading.Event()
        self._run_thread = threading.Thread(target=self._run)
        self._run_thread.start()
        logger.debug("FeedProcessor initialised")

    def register_client(self, client: ConnectedClient) -> None:
        if self._stop_event.is_set():
            raise FeedProcessorStoppedError("Cannot register new client")

        client_id = client.client_id
        with self._lock:
            self._clients.add(client_id)

        logger.debug(f"Registered new client {client_id}")

    def unregister_client(self, client_id: uuid.UUID) -> None:
        if client_id not in self._clients:
            logger.error(f"Cannot unregister unknown client {client_id}")
            return

        with self._lock:
            self._clients.remove(client_id)

        # TODO: What is queue is full?
        self._task_queue.put(ClientDisconnectedMessage(client_id))

    def enqueue_frame_for_processing(
        self, client_id: uuid.UUID, frame: np.ndarray
    ) -> None:
        if self._stop_event.is_set():
            raise FeedProcessorStoppedError(
                f"Cannot process frame from client {client_id}, "
                f"Processing is stopping"
            )
        if client_id not in self._clients:
            raise KeyError(
                f"Client {client_id} is not registered with the Processor"
            )

        # TODO: What is queue is full?
        self._task_queue.put(ProcessFrameMessage(client_id, frame))

    # TODO: This guy is sequential, could we make it better?
    def _run(self) -> None:
        logger.debug("Processor started")

        while not self._stop_event.is_set():
            batch: List[ProcessFrameMessage] = self._collect_batch()
            if not len(batch):
                time.sleep(0.1)
                continue
            logger.debug("Bot a batch of frames")

            detections = self._model([item.frame for item in batch])
            for detection, item in zip(detections, batch):
                item.detections = detection

            logger.debug("Scored the model")
            self._result_queue.put(batch)

        logger.debug("Processor stopped")

    def _collect_batch(self) -> List[ProcessFrameMessage]:
        time_window = self._time_window
        batch_size = self._batch_size
        queue = self._task_queue
        batch: List[ProcessFrameMessage] = []
        while time_window > 0:
            if len(batch) == batch_size:
                return batch
            start_time = time.perf_counter()
            try:
                message = queue.get(timeout=time_window)
            except Empty:
                break

            if isinstance(message, ProcessFrameMessage):
                batch.append(message)
            elif isinstance(message, ClientDisconnectedMessage):
                self._result_queue.put(message)

            time_window -= time.perf_counter() - start_time
        return batch

    def stop(self, timeout: Optional[float] = None) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
            self._run_thread.join(timeout=timeout)
            if self._run_thread.is_alive():
                logger.error("Processor failed to stop in reasonable time")
            else:
                logger.debug("Processor stopped gracefully")
        else:
            logger.warning("Called stop on already stopping Processor")
