import enum
from queue import Queue
import os
import threading
from typing import List

from watchdawg.util.logger import get_logger
from watchdawg.backend.messages import ProcessFrameMessage


logger = get_logger("results_writer")


"""
Each CV2 window will need to be run by a dedicated thread as frames will arrive
at different time with different speed etc

Create a thread for each client id?
"""


class ResultWriterMode(enum.Enum):
    SHOW_FRAMES = 1
    SAVE_FRAMES = 2
    SHOW_AND_SAVE_FRAMES = 3


class ResultsWriter:
    def __init__(
        self,
        processed_frames_queue: Queue,
        mode: ResultWriterMode,
        save_folder: str,
    ) -> None:
        self._queue = processed_frames_queue
        self._mode = mode
        self._save_folder = save_folder
        self._prepare()

        self._stop_event = threading.Event()
        self._run_thread = threading.Thread(target=self._run)
        self._run_thread.start()
        logger.debug("ResultsWriter initialised")

    def _prepare(self) -> None:
        if self._mode in [
            ResultWriterMode.SAVE_FRAMES,
            ResultWriterMode.SHOW_AND_SAVE_FRAMES,
        ] and not os.path.exists(self._save_folder):
            os.mkdir(self._save_folder)
            logger.debug(f"Created folder {self._save_folder} to save feed to")

    def _run(self) -> None:
        logger.debug("ResultsWriter started")

        while not self._stop_event.is_set():
            batch = self._queue.get()
            self._process_detections(batch)

        logger.debug("ResultsWriter finished")

    def _process_detections(self, batch: List[ProcessFrameMessage]) -> None:
        for item in batch:
            # TODO: Draw
            _ = (
                item.client_id,
                item.frame,
                item.detections,
            )

            # TODO: HERE - Direct the item to the worker to show/write
            #       this frame!

    def stop(self, timeout: float) -> None:
        if not self._stop_event.is_set():
            self._stop_event.set()
            self._run_thread.join(timeout=timeout)
            if self._run_thread.is_alive():
                logger.error("ResultsWriter failed to stop in reasonable time")
            else:
                logger.debug("ResultsWriter stopped gracefully")
        else:
            logger.warning("Called stopp on already stopping ResultsWriter")
