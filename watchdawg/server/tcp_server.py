from typing import List, Callable
import struct
import pickle
from datetime import datetime
import threading
import time

import cv2

from watchdawg.server.base import BaseServer, ConnectedClient
from watchdawg.util.logger import get_logger
from watchdawg.util.communication import create_socket
from watchdawg.config import Config


logger = get_logger("tcp_server")


"""
TODO:
Keep track of clients (reconnections)
Different modes (show frames, save to disk, transmit to FE etc)
Monitor threads
Unhashable ConnectedClient, I dont like List though
"""


class TCPServer(BaseServer):
    def __init__(
        self,
        port: int = Config.SERVER_PORT,
        state_report_frequency: int = Config.SERVER_STATE_REPORT_FREQUENCY,
    ) -> None:
        self._socket = create_socket()
        self._socket.bind(("", port))

        self._lock = threading.Lock()
        self._connected_clients: List[ConnectedClient] = []

        monitor = threading.Thread(
            name="State reporter",
            target=self._monitor_thread,
            args=(state_report_frequency,),
            daemon=True,
        )
        monitor.start()
        logger.info("TCP server initialised")

    def start_server(self) -> None:
        self._socket.listen()
        logger.info("TCP server started, listening for connections")

        while True:
            conn, address = self._socket.accept()
            logger.info(f"Server got connection from {address}")

            # TODO: Consider getting client name and checking whether we want
            #       to serve it (known client - camera)

            new_client = ConnectedClient(
                connection=conn, connected_at=datetime.now(), address=address
            )
            thread = threading.Thread(
                name=f"Client {address[0]}:{address[1]}",
                target=self._safe_handle_client,
                args=(new_client, self._handle_client),
                daemon=True,
            )
            thread.start()

    def _safe_handle_client(
        self,
        client: ConnectedClient,
        handle_func: Callable[[ConnectedClient], None],
    ) -> None:
        self._thread_safe_call(lambda: self._connected_clients.append(client))
        thread_name = (
            f"<Thread (name: {threading.current_thread().name}, "
            f"indent: {threading.get_ident()})>"
        )
        logger.info(f"{thread_name} started to handle client {client.address}")
        try:
            handle_func(client)
        except Exception as e:
            logger.error(
                f"{thread_name} failed while processing client "
                f"{client.address}. Error: {e}"
            )
        else:
            logger.info(f"Client {client.address} disconnected")

        self._thread_safe_call(lambda: self._connected_clients.remove(client))
        logger.debug(f"{thread_name} finished")

    def _handle_client(self, client: ConnectedClient) -> None:
        conn = client.connection
        data = b""
        payload_size = struct.calcsize(Config.STRUCT_SIZE_FORMAT)
        window_name = f"Client {client.address}"
        while True:
            while len(data) < payload_size:
                data += conn.recv(4096)
                if not data:
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
            cv2.imshow(window_name, frame)
            cv2.waitKey(1)
        cv2.destroyWindow(window_name)

    def _monitor_thread(self, interval: int) -> None:
        logger.info(
            f"Monitor thread started, reporting every {interval} seconds"
        )
        while True:
            time.sleep(interval)
            logger.info(
                f"Connected clients: {len(self._connected_clients)}; "
                f"Active threads: {threading.active_count()}"
            )

    def _thread_safe_call(self, func: Callable) -> None:
        with self._lock:
            func()

    def stop(self) -> None:
        # TODO: Report connected clients?
        # TODO: How to stop gracefully?

        logger.info("Stopping the server")
        self._socket.close()
