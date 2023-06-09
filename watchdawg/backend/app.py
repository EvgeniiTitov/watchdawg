import time
import threading
from queue import Queue

from watchdawg.backend.server import TCPServer
from watchdawg.backend.feed_processor import FeedProcessor
from watchdawg.backend.results_writer import ResultsWriter, ResultWriterMode
from watchdawg.config import Config
from watchdawg.util.resources import (
    get_current_process_ram_usage,
    get_current_process_cpu_usage,
)
from watchdawg.backend.messages import BusMessage
from watchdawg.util.logger import get_logger
from watchdawg.backend.model import UltralyticsYOLO


logger = get_logger("app")


class App:
    def __init__(
        self,
        mode: ResultWriterMode,
        save_feed_folder: str = Config.PROCESSED_FEED_LOCAL_FOLDER,
    ) -> None:
        self._server_processor_bus: "Queue[BusMessage]" = Queue(
            Config.DECODED_FRAMES_QUEUE_SIZE
        )
        self.processor_writer_bus: "Queue[BusMessage]" = Queue(
            Config.PROCESSED_BATCHES_QUEUE_SIZE
        )
        self._server = TCPServer(
            events_queue=self._server_processor_bus, port=Config.SERVER_PORT
        )
        self._feed_processor = FeedProcessor(
            events_queue_in=self._server_processor_bus,
            batch_size=Config.MODEL_BATCH_SIZE,
            build_batch_time_window=Config.BUILD_BATCH_TIME_WINDOW,
            events_queue_out=self.processor_writer_bus,
            model=UltralyticsYOLO(model="yolov8n.pt"),
        )
        self._feed_processor.name = "FeedProcessor"  # Thread name

        self._results_writer = ResultsWriter(
            events_queue_in=self.processor_writer_bus,
            mode=mode,
            save_folder=save_feed_folder,
        )
        self._results_writer.name = "ResultsWriter"  # Thread name

        self._reporter_thread = threading.Thread(
            name="StateReporter",
            target=self._report_state,
            args=(Config.REPORT_STATE_FREQUENCY,),
            daemon=True,
        )
        logger.info("App initialised")

    def start(self):
        self._results_writer.start()
        self._feed_processor.start()
        self._server.start_server()
        self._reporter_thread.start()

    def stop(self):
        self._server.stop_server()
        self._feed_processor.stop()
        self._results_writer.stop()

        self._feed_processor.join(timeout=2.0)
        if self._feed_processor.is_alive():
            logger.error("Failed to stop FeedProcessor in reasonable time")

        self._results_writer.join(timeout=2.0)
        if self._results_writer.is_alive():
            logger.error("Failed to stop ResultsWriter in reasonable time")

        logger.info("App shutdown")

    def _report_state(self, interval: int) -> None:
        while True:
            time.sleep(interval)

            # TODO: Measure CPU usage over interval - blocking?
            # TODO: Add network usage
            cpu_usage = get_current_process_cpu_usage()
            memory_usage = get_current_process_ram_usage()
            logger.info(
                f"Connected clients: {self._server.total_connected_clients}; "
                f"Active threads: {threading.active_count()} "
                f"({', '.join([thread.name for thread in threading.enumerate()])}); "  # noqa
                f"CPU usage: {cpu_usage}%; "
                f"Memory usage (MB): {memory_usage: .2f}; "
                f"Server-processor queue: {self._server_processor_bus.qsize()}; "  # noqa
                f"Processor-writer queue: {self._server_processor_bus.qsize()}; "  # noqa
                f"ResultWriter handler queues: "
                f"{self._results_writer.report_handlers_queue_size()}"
            )
