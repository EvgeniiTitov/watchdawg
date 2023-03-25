from typing import List, Callable
import struct
import pickle
from datetime import datetime
import threading

import cv2

from watchdawg.server.base import BaseServer, ConnectedClient
from watchdawg.util.logger import get_logger
from watchdawg.util.communication import create_socket
from watchdawg.config import Config


logger = get_logger("tcp_server")


"""
TODO:

Multiple clients (threads)
Keep track of clients (reconnections)
Clients must introduce themselves
Different modes (show frames, save to disk, transmit to FE etc)
Monitor threads
Unhashable ConnectedClient, I dont like List though
"""


class TCPServer(BaseServer):
    def __init__(self, port: int = Config.SERVER_PORT) -> None:
        self._socket = create_socket()
        self._socket.bind(("", port))

        self._connected_clients: List[ConnectedClient] = []
        logger.info("TCP server initialised")

    def start_server(self) -> None:
        self._socket.listen()
        logger.info("TCP server started, listening for connections")

        while True:
            conn, address = self._socket.accept()
            logger.info(f"Got connection from {address}")
            new_client = ConnectedClient(
                connection=conn, connected_at=datetime.now(), address=address
            )
            self._connected_clients.append(new_client)
            thread = threading.Thread(
                name=f"Client {address}",
                target=self._safe_handle_client,
                args=(new_client, self._handle_client),
                daemon=True,  # TODO: What do we do here?
            )
            thread.start()

    def _safe_handle_client(
        self,
        client: ConnectedClient,
        handle_func: Callable[[ConnectedClient], None],
    ) -> None:
        thread_name = threading.get_ident()
        logger.info(f"Thread {thread_name} started to handle client {client}")
        try:
            handle_func(client)
        except Exception as e:
            logger.error(
                f"Thread {thread_name} failed while processing client "
                f"{client}. Error: {e}"
            )
        else:
            logger.info(f"Client {client} disconnected")

        self._connected_clients.remove(client)
        logger.debug(f"Thread {thread_name} finished")

    def _handle_client(self, client: ConnectedClient) -> None:
        conn = client.connection
        data = b""
        payload_size = struct.calcsize(Config.STRUCT_SIZE_FORMAT)
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

            cv2.imshow(f"Client {client.address}", frame)
            cv2.waitKey(1)

    def stop(self) -> None:
        logger.info("Stopping the server")
        self._socket.close()
