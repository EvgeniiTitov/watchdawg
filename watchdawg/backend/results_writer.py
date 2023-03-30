import enum
import uuid
from queue import Queue, Empty, Full
import os
import threading
from typing import MutableMapping, Tuple, Union, List

import numpy as np
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

    def report_handlers_queue_size(self) -> List[Tuple[uuid.UUID, int]]:
        queue_sizes = []
        for client, (queue, _) in self._client_handlers.items():
            queue_sizes.append((client, queue.qsize()))
        return queue_sizes

    def run(self) -> None:
        logger.debug("ResultsWriter started")

        while not self._stop_event.is_set():
            try:
                message = self._queue.get(timeout=0.5)
            except Empty:
                continue

            if isinstance(message, NewClientConnectedMessage):
                self._connect_new_client(message)
            elif isinstance(message, ClientDisconnectedMessage):
                self._disconnect_client(message)
            elif isinstance(message, FramesBatchMessage):
                self._process_batch(message)

        logger.debug("ResultsWriter finished")

    def _connect_new_client(self, message: NewClientConnectedMessage) -> None:
        client_id = message.client_id
        address = f"{message.address[0]}:{message.address[1]}"
        if client_id in self._client_handlers:
            logger.error(
                "Client with such ID already exists and is being processed"
            )
            return

        client_queue: "Queue[Union[np.ndarray, ClientDisconnectedMessage]]" = (
            Queue(Config.CLIENT_RESULT_WRITER_HANDLER_QUEUE)
        )
        handler_thread = threading.Thread(
            name=f"ResultWriterClientHandler_{address}",
            target=self._safe_handle_processed_client_data,
            args=(
                message,
                client_queue,
            ),
        )
        handler_thread.start()

        self._client_handlers[client_id] = (
            client_queue,
            handler_thread,
        )

    def _disconnect_client(self, message: ClientDisconnectedMessage) -> None:
        client_id = message.client_id
        if client_id not in self._client_handlers:
            logger.error("Cannot disconnected not connected client")
            return

        client_queue, _ = self._client_handlers[client_id]
        # TODO: This is blocking
        client_queue.put(message)

        # TODO: This naively assumes the thread will exit, no joining? Can leak
        del self._client_handlers[client_id]

    def _process_batch(self, batch: FramesBatchMessage) -> None:
        for item in batch.batch:
            client_id = item.client_id
            frame = item.frame
            detections = item.detections

            if detections:
                # TODO: Draw detections of the frame
                pass

            # TODO: Is there a better solution than dropping frames?
            try:
                self._client_handlers[client_id][0].put_nowait(frame)
            except Full:
                logger.warning("Client handler queue is full, dropping frames")
                continue
            except Exception as e:
                logger.error(
                    f"Error occurred while directing frame to its "
                    f"handler. Error: {e}"
                )
                continue

    def _safe_handle_processed_client_data(
        self, client: NewClientConnectedMessage, client_queue: Queue
    ) -> None:
        """A wrapper to catch any exceptions happening in a thread to avoid
        leaking memory
        """
        client_id = client.client_id
        logger.debug(
            f"ResultsWriter thread handling client {client_id} started"
        )
        try:
            self._handle_processed_client_data(client, client_queue)
        except Exception as e:
            logger.error(
                f"ResultWriter handler processing client {client_id} failed "
                f"with error: {e}"
            )
        logger.debug(
            f"ResultsWriter thread handling client {client_id} stopped"
        )

    def _handle_processed_client_data(
        self, client: NewClientConnectedMessage, client_queue: Queue
    ) -> None:
        client_id = client.client_id
        client_address = f"{client.address[0]}:{client.address[1]}"
        is_visual_mode = self._mode in {
            ResultWriterMode.SHOW_FRAMES,
            ResultWriterMode.SHOW_AND_SAVE_FRAMES,
        }
        is_disk_mode = self._mode in {
            ResultWriterMode.SAVE_FRAMES,
            ResultWriterMode.SHOW_AND_SAVE_FRAMES,
        }
        if is_visual_mode:
            window_name = f"Client - {client_address}"
            cv2.namedWindow(window_name)

        if is_disk_mode:
            filename = os.path.join(
                self._save_folder, f"{client_address}_{client_id}_feed.avi"
            )
            video_out = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*"MJPG"),
                Config.SAVE_VIDEO_FPS,
                (Config.SAVE_VIDEO_WIDTH, Config.SAVE_VIDEO_HEIGHT),
            )

        while True:
            message = client_queue.get()
            if isinstance(message, ClientDisconnectedMessage):
                break

            if is_visual_mode:
                cv2.imshow(window_name, message)
                cv2.waitKey(1)

            if is_disk_mode:
                video_out.write(message)

        if is_visual_mode:
            cv2.destroyWindow(window_name)
        if is_disk_mode:
            video_out.release()

    def _draw_detections(self, batch: FramesBatchMessage) -> None:
        # TODO: Draw bounding boxes etc
        pass

    def stop(self) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
        else:
            logger.warning("Called stop on already stopping ResultsWriter")
