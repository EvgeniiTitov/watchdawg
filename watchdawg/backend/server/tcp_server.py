import uuid
from typing import Set
import struct
import pickle
from datetime import datetime
import threading
from queue import Queue

import cv2

from watchdawg.backend.server.interface import BaseServer
from watchdawg.backend.messages import (
    ProcessFrameMessage,
    ClientDisconnectedMessage,
    NewClientConnectedMessage,
)
from watchdawg.backend.connected_client import ConnectedClient
from watchdawg.util.logger import get_logger
from watchdawg.util.communication import create_socket
from watchdawg.config import Config


logger = get_logger("tcp_server")


class TCPServer(BaseServer):
    def __init__(self, events_queue: Queue, port: int) -> None:
        self._socket = create_socket()
        self._socket.bind(("", port))

        self._events_queue = events_queue
        self._connected_clients: Set[uuid.UUID] = set()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        logger.debug("TCP server initialised")

    @property
    def total_connected_clients(self) -> int:
        return len(self._connected_clients)

    def start_server(self) -> None:
        self._accept_conns_thread = threading.Thread(
            name="TCPServer", target=self._accept_connections, daemon=True
        )
        self._accept_conns_thread.start()

    def _accept_connections(self) -> None:
        logger.info("TCP server started")
        self._socket.listen()

        logger.info("Listening for incoming connections...")
        while not self._stop_event.is_set():
            conn, address = self._socket.accept()
            # .accept() is blocking
            if self._stop_event.is_set():
                break

            logger.info(f"Received connection from {address}")

            client_id = uuid.uuid4()
            new_client = ConnectedClient(
                client_id=client_id,
                connection=conn,
                connected_at=datetime.now(),
                address=address,
            )
            thread = threading.Thread(
                name=f"TCP client {address}",
                target=self._safe_handle_client,
                args=(new_client,),
                daemon=True,
            )
            thread.start()

    def _safe_handle_client(self, client: ConnectedClient) -> None:
        """To avoid leaking threads, ensure they complete even in case of a
        failure.
        """
        client_id = client.client_id
        thread_name = f"Thread {threading.get_ident()}"
        logger.debug(
            f"{thread_name} started to handle client {client.address}"
        )
        self._events_queue.put(
            NewClientConnectedMessage(client_id, client.address)
        )
        with self._lock:
            self._connected_clients.add(client_id)

        try:
            self._serve_client(client)
        except Exception as e:
            logger.error(
                f"{thread_name} failed while processing client "
                f"{client.address}. Error: {e}"
            )

        self._events_queue.put(
            ClientDisconnectedMessage(client_id, client.address)
        )
        with self._lock:
            self._connected_clients.remove(client_id)

        logger.debug(f"{thread_name} finished with client {client.address}")

    def _serve_client(self, client: ConnectedClient) -> None:
        conn = client.connection
        client_id = client.client_id
        data = b""
        payload_size = struct.calcsize(Config.STRUCT_SIZE_FORMAT)
        while not self._stop_event.is_set():
            while len(data) < payload_size:
                data += conn.recv(4096)
                if not data:
                    logger.debug(f"Client {client.address} disconnected")
                    return

            packed_message_size = data[:payload_size]
            data = data[payload_size:]
            message_size = struct.unpack(
                Config.STRUCT_SIZE_FORMAT, packed_message_size
            )[0]

            while len(data) < message_size:
                data += conn.recv(4096)

            frame_data = data[:message_size]
            data = data[message_size:]
            frame = pickle.loads(
                frame_data, fix_imports=True, encoding="bytes"
            )
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            self._events_queue.put(
                ProcessFrameMessage(client_id=client_id, frame=frame)
            )

    def stop_server(self) -> None:
        self._stop_event.set()
        self._socket.close()
        logger.info("TCPServer stopped")
