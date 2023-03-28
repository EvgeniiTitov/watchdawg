import uuid
from typing import List, Callable
import struct
import pickle
from datetime import datetime
import threading
import time

import cv2

from watchdawg.backend.server.interface import BaseServer
from watchdawg.backend.messages import ConnectedClient
from watchdawg.util.logger import get_logger
from watchdawg.util.communication import create_socket
from watchdawg.util.resources import (
    get_current_process_ram_usage,
    get_current_process_cpu_usage,
)
from watchdawg.config import Config
from watchdawg.backend.feed_processor import FeedProcessor


logger = get_logger("tcp_server")


class TCPServer(BaseServer):
    def __init__(
        self,
        feed_processor: FeedProcessor,
        port: int = Config.SERVER_PORT,
        state_report_frequency: int = Config.SERVER_STATE_REPORT_FREQUENCY,
    ) -> None:
        self._socket = create_socket()
        self._socket.bind(("", port))

        self._feed_processor = feed_processor
        self._lock = threading.Lock()

        # TODO: Could we replace list with something quicket?
        self._connected_clients: List[ConnectedClient] = []

        self._stop_event = threading.Event()
        # TODO: Consider keeping track of threads (not daemons), make sockets
        #       not blocking and manage threads if there are no connections
        monitor = threading.Thread(
            name="State reporter",
            target=self._monitor_thread,
            args=(state_report_frequency,),
            daemon=True,
        )
        monitor.start()
        logger.debug("TCP server initialised")

    def start_server(self) -> None:
        logger.info("TCP server started, listening for connections...")

        self._socket.listen()
        while not self._stop_event.is_set():
            conn, address = self._socket.accept()
            logger.info(f"Received connection from {address}")

            client_id = uuid.uuid4()
            new_client = ConnectedClient(
                client_id=client_id,
                connection=conn,
                connected_at=datetime.now(),
                address=address,
            )
            thread = threading.Thread(
                target=self._safe_handle_client,
                args=(new_client,),
                daemon=True,
            )
            thread.start()

        logger.debug("TCP server stopped")

    def _safe_handle_client(self, client: ConnectedClient) -> None:
        """To avoid leaking threads, ensure they complete even if they fail"""
        thread_name = f"Thread {threading.get_ident()}"
        logger.debug(
            f"{thread_name} started to handle client {client.address}"
        )
        self._thread_safe_call(lambda: self._connected_clients.append(client))
        try:
            self._feed_processor.register_client(client)
            self._serve_client(client)
        except Exception as e:
            logger.error(
                f"{thread_name} failed while processing client "
                f"{client.address}. Error: {e}"
            )
        self._feed_processor.unregister_client(client.client_id)
        self._thread_safe_call(lambda: self._connected_clients.remove(client))
        logger.debug(f"{thread_name} finished with client {client.address}")

    def _serve_client(self, client: ConnectedClient) -> None:
        conn = client.connection
        client_id = client.client_id
        data = b""
        payload_size = struct.calcsize(Config.STRUCT_SIZE_FORMAT)
        while True:
            while len(data) < payload_size:
                data += conn.recv(4096)
                if not data:
                    logger.debug(f"Client {client.address} disconnected")
                    return

            # Receive image raw data from client socket
            packed_message_size = data[:payload_size]
            data = data[payload_size:]
            message_size = struct.unpack(
                Config.STRUCT_SIZE_FORMAT, packed_message_size
            )[0]

            while len(data) < message_size:
                data += conn.recv(4096)

            frame_data = data[:message_size]
            data = data[message_size:]

            # Unpickle image
            frame = pickle.loads(
                frame_data, fix_imports=True, encoding="bytes"
            )
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            self._feed_processor.enqueue_frame_for_processing(
                client_id=client_id, frame=frame
            )

    def _monitor_thread(self, interval: int) -> None:
        logger.debug(
            f"Monitor thread started, reporting every {interval} seconds"
        )
        while True:
            time.sleep(interval)
            # TODO: Measure CPU usage over interval - blocking?
            # TODO: Add network usage
            cpu_usage = get_current_process_cpu_usage()
            memory_usage = get_current_process_ram_usage()
            logger.info(
                f"Connected clients: {len(self._connected_clients)}; "
                f"Active threads: {threading.active_count()}; "
                f"CPU usage: {cpu_usage}%; "
                f"Memory usage (MB): {memory_usage}"
            )

    def _thread_safe_call(self, func: Callable) -> None:
        with self._lock:
            func()

    def stop_server(self) -> None:
        # TODO: Report still connected clients?
        # TODO: Stop everything gracefully

        logger.info("Stopping the server")
        self._stop_event.set()
        self._socket.close()
