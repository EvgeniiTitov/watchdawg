import struct
import pickle

import cv2

from watchdawg.server import BaseServer
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
"""


class TCPServer(BaseServer):
    def __init__(self, port: int = Config.SERVER_PORT) -> None:
        self._socket = create_socket()
        self._socket.bind(("", port))
        logger.info("TCP server initialised")

    def start_server(self) -> None:
        self._socket.listen()
        logger.info("TCP server started, listening for connections")

        conn, address = self._socket.accept()
        logger.info(f"Got connection from {address}")

        data = b""
        payload_size = struct.calcsize(Config.STRUCT_SIZE_FORMAT)
        logger.debug(f"Payload size: {payload_size}")

        while True:

            while len(data) < payload_size:
                data += conn.recv(4096)
                if not data:
                    cv2.destroyAllWindows()
                    conn, address = self._socket.accept()
                    continue

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

            cv2.imshow("client name here", frame)
            cv2.waitKey(1)

    def stop(self) -> None:
        logger.info("Stopping the server")
        self._socket.close()
