import time
from typing import List
from queue import Queue, Empty
import threading

from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import (
    ClientDisconnectedMessage,
    ProcessFrameMessage,
    NewClientConnectedMessage,
    FramesBatchMessage,
)


logger = get_logger("feed_processor")


class FeedProcessor(threading.Thread):
    def __init__(
        self,
        events_queue_in: Queue,
        batch_size: int,
        build_batch_time_window: float,
        events_queue_out: Queue,
        model,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._events_queue_in = events_queue_in
        self._batch_size = batch_size
        self._time_window = build_batch_time_window
        self._events_queue_out = events_queue_out
        self._model = model
        self._stop_event = threading.Event()
        logger.debug("FeedProcessor initialised")

    # TODO: Batches are processed sequentially, parallelize?
    def run(self) -> None:
        logger.debug("Processor started")

        while not self._stop_event.is_set():
            frames_batch: FramesBatchMessage = self._collect_batch()
            if not len(frames_batch.batch):
                time.sleep(0.1)
                continue

            detections = self._model(
                [item.frame for item in frames_batch.batch]
            )
            for detection, frame_message in zip(
                detections, frames_batch.batch
            ):
                frame_message.detections = detection

            self._events_queue_out.put(frames_batch)

        logger.debug("Processor stopped")

    def _collect_batch(self) -> FramesBatchMessage:
        time_window = self._time_window
        batch_size = self._batch_size
        queue = self._events_queue_in

        batch: List[ProcessFrameMessage] = []
        while time_window > 0:
            if len(batch) == batch_size:
                return FramesBatchMessage(batch)

            start_time = time.perf_counter()
            try:
                message = queue.get(timeout=time_window)
            except Empty:
                break

            # TODO: BUG! Disconnection message gets sent while we might wait
            #       a bit more (time window), before sending frames for already
            #       disconnected client to RW!

            if isinstance(message, ProcessFrameMessage):
                batch.append(message)
            elif isinstance(
                message,
                (
                    NewClientConnectedMessage,
                    ClientDisconnectedMessage,
                ),
            ):
                self._events_queue_out.put(message)

            time_window -= time.perf_counter() - start_time
        return FramesBatchMessage(batch)

    def stop(self) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
        else:
            logger.warning("Called stop on already stopping Processor")
