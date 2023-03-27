import time
from typing import Set, Optional, List
import uuid
from queue import Queue, Empty
import threading

import numpy as np

from watchdawg.backend.feed_processor.interface import BaseFeedProcessor
from watchdawg.backend.results_writer.interface import BaseResultsWriter
from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import (
    ClientDisconnectedMessage,
    ProcessFrameMessage,
    ConnectedClient,
    FeedProcessorMessage,
)
from watchdawg.backend.exceptions import FeedProcessorStoppedError


logger = get_logger("feed_processor")


TODO_MODEL = lambda batch: batch  # noqa


class FeedProcessor(BaseFeedProcessor):
    def __init__(
        self,
        frame_queue_size: int,
        batch_size: int,
        build_batch_time_window: float,
        results_writer: BaseResultsWriter,
        model=TODO_MODEL,
    ) -> None:
        self._queue: "Queue[FeedProcessorMessage]" = Queue(
            maxsize=frame_queue_size
        )
        self._batch_size = batch_size
        self._time_window = build_batch_time_window
        self._model = model
        self._results_writer = results_writer

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

        self._results_writer.register_client(client)

        logger.debug(f"Registered new client {client_id}")

    def unregister_client(self, client_id: uuid.UUID) -> None:
        if client_id not in self._clients:
            logger.error(f"Cannot unregister unknown client {client_id}")
            return

        with self._lock:
            self._clients.remove(client_id)

        # TODO: What is queue is full?
        self._queue.put(ClientDisconnectedMessage(client_id))

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
        self._queue.put(ProcessFrameMessage(client_id, frame))

    # TODO: This guy is sequential, could we make it better?
    def _run(self) -> None:
        logger.debug("Processor started")

        while not self._stop_event.is_set():
            batch: List[np.ndarray] = self._collect_batch()
            if not len(batch):
                time.sleep(0.05)
                continue

            logger.debug("Bot a batch of frames")
            results = self._model(batch)  # TODO: Must return detections
            self._results_writer.process_batch(batch, results)

    def _collect_batch(self) -> List[np.ndarray]:
        time_window = self._time_window
        batch_size = self._batch_size
        queue = self._queue
        batch: List[np.ndarray] = []
        while time_window > 0:
            if len(batch) == batch_size:
                return batch
            start_time = time.perf_counter()
            try:
                message = queue.get(timeout=time_window)
            except Empty:
                break

            if isinstance(message, ProcessFrameMessage):
                batch.append(message.frame)
            elif isinstance(message, ClientDisconnectedMessage):
                self._results_writer.unregister_client(message.client_id)

            time_window -= time.perf_counter() - start_time
        return batch

    def stop(self, timeout: Optional[float] = None) -> None:
        self._stop_event.set()
        self._run_thread.join(timeout=timeout)
        if self._run_thread.is_alive():
            logger.error("Failed to stop Processor in reasonable time")
        else:
            logger.debug("Processor stopped gracefully")
