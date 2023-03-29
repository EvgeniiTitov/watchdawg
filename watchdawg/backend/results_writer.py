import enum
import uuid
from queue import Queue, Empty, Full
import os
import threading
from typing import MutableMapping, Tuple

import cv2

from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import (
    NewClientConnectedMessage,
    ClientDisconnectedMessage,
    FramesBatchMessage,
)
from watchdawg.config import Config


logger = get_logger("results_writer")


class ResultWriterMode(enum.Enum):
    SHOW_FRAMES = 1
    SAVE_FRAMES = 2
    SHOW_AND_SAVE_FRAMES = 3


class ResultsWriter(threading.Thread):
    def __init__(
        self,
        events_queue_in: Queue,
        mode: ResultWriterMode,
        save_folder: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._queue = events_queue_in
        self._mode = mode
        self._save_folder = save_folder
        self._stop_event = threading.Event()
        self._client_handlers: MutableMapping[
            uuid.UUID, Tuple[Queue, threading.Thread]
        ] = {}
        self._prepare()
        logger.debug("ResultsWriter initialised")

    def _prepare(self) -> None:
        if self._mode in [
            ResultWriterMode.SAVE_FRAMES,
            ResultWriterMode.SHOW_AND_SAVE_FRAMES,
        ] and not os.path.exists(self._save_folder):
            os.mkdir(self._save_folder)
            logger.debug(f"Created folder {self._save_folder} to save feed to")

    def run(self) -> None:
        logger.debug("ResultsWriter started")

        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=0.5)
            except Empty:
                continue

            if isinstance(message, NewClientConnectedMessage):
                client_id = message.client_id
                if client_id in self._client_handlers:
                    logger.error("Client with such ID already being processed")
                    continue

                client_queue = Queue(Config.CLIENT_QUEUE)  # type: ignore
                handler_thread = threading.Thread(
                    target=self._handle_client_data,
                    args=(client_id, client_queue,)
                )
                handler_thread.start()
                self._client_handlers[client_id] = (
                    client_queue,
                    handler_thread,
                )

            elif isinstance(message, ClientDisconnectedMessage):
                client_id = message.client_id
                client_queue, _ = self._client_handlers[client_id]

                # TODO: This is blocking
                client_queue.put(ClientDisconnectedMessage)

                # TODO: This naively assumes the thread will exit, no joining?
                del self._client_handlers[client_id]

            elif isinstance(message, FramesBatchMessage):
                self._draw_detections(message)
                for item in message.batch:
                    client_id = item.client_id
                    frame = item.frame
                    # TODO: Blocking

                    try:
                        self._client_handlers[client_id][0].put_nowait(frame)
                    except Full:
                        logger.warning(
                            "Client handler queue is full, dropping frames"
                        )
                        continue
                    except Exception as e:
                        logger.error(
                            f"Error occurred while directing frame to its "
                            f"handler. Error: {e}"
                        )
                        continue

        logger.debug("ResultsWriter finished")

    def _handle_client_data(
        self, client_id: uuid.UUID, client_queue: Queue
    ) -> None:
        logger.debug(
            f"ResultsWriter thread handling client {client_id} started"
        )
        window_name = f"Client {client_id}"
        cv2.namedWindow(window_name)

        while True:
            message = client_queue.get()
            if isinstance(message, ClientDisconnectedMessage):
                break
            else:
                if self._mode == ResultWriterMode.SHOW_FRAMES:
                    cv2.imshow(window_name, message)
                    cv2.waitKey(1)
                elif self._mode == ResultWriterMode.SAVE_FRAMES:
                    # TODO: Save
                    pass
                else:
                    # TODO: Show and save on disk
                    pass

        cv2.destroyWindow(window_name)
        logger.debug(
            f"ResultsWriter thread handling client {client_id} stopped"
        )

    def _draw_detections(self, batch: FramesBatchMessage) -> None:
        # TODO: Draw bounding boxes etc
        pass

    def stop(self) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
        else:
            logger.warning("Called stop on already stopping ResultsWriter")
