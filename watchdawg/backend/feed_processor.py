import time
from typing import Optional, List, Tuple
from queue import Queue, Empty
import threading

from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import (
    ClientDisconnectedMessage,
    ProcessFrameMessage,
    NewClientConnectedMessage,
    FramesBatchMessage,
)
from watchdawg.backend.model import MLModel


logger = get_logger("feed_processor")


class FeedProcessor(threading.Thread):
    def __init__(
        self,
        events_queue_in: Queue,
        batch_size: int,
        build_batch_time_window: float,
        events_queue_out: Queue,
        model: MLModel,
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
            frames_batch, disconnected_client = self._collect_batch()

            if disconnected_client:
                self._events_queue_out.put(disconnected_client)

            if not len(frames_batch):
                continue

            # detections = self._model([item.frame for item in frames_batch])
            # for detection, frame_message in zip(detections, frames_batch):
            #     frame_message.detections = detection

            # TODO: A lot of overhead with Ultralytics (copies etc)
            # ULTRALYTICS draw BB for us
            processed_frames = self._model(
                [item.frame for item in frames_batch]
            )
            for processed_frame, frame_message in zip(
                processed_frames, frames_batch
            ):
                frame_message.frame = processed_frame

            self._events_queue_out.put(FramesBatchMessage(frames_batch))

        logger.debug("Processor stopped")

    def _collect_batch(
        self,
    ) -> Tuple[List[ProcessFrameMessage], Optional[ClientDisconnectedMessage]]:
        time_window = self._time_window
        batch_size = self._batch_size
        queue = self._events_queue_in

        batch: List[ProcessFrameMessage] = []
        while time_window > 0:
            if len(batch) == batch_size:
                return batch, None

            start_time = time.perf_counter()
            try:
                message = queue.get(timeout=time_window)
            except Empty:
                break

            if isinstance(message, ProcessFrameMessage):
                batch.append(message)
            elif isinstance(message, NewClientConnectedMessage):
                self._events_queue_out.put(message)
            elif isinstance(message, ClientDisconnectedMessage):
                # If a client disconnected, stop collecting a batch and
                # return to propagate this info downstream asap. A batch might
                # not be full, but clients don't disconnect often, so it's ok
                return batch, message

            time_window -= time.perf_counter() - start_time
        return batch, None

    def stop(self) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
        else:
            logger.warning("Called stop on already stopping Processor")
