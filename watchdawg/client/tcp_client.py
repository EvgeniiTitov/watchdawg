from typing import Optional
import pickle
import struct

import cv2

from watchdawg.client import BaseClient
from watchdawg.source import BaseSource
from watchdawg.util.logger import get_logger
from watchdawg.util.communication import create_socket, connect_to_server
from watchdawg.preprocessor import BaseFramePreprocessor
from watchdawg.config import Config


logger = get_logger(name="tcp_client")


class TCPClient(BaseClient):
    def __init__(
        self,
        name: str,
        video_source: BaseSource,
        frame_preprocessor: Optional[BaseFramePreprocessor] = None,
        server_host: str = Config.SERVER_HOST,
        server_port: int = Config.SERVER_PORT,
        every_nth_frame: int = 0
    ) -> None:
        super().__init__(
            name, video_source, frame_preprocessor, every_nth_frame
        )
        self._socket = create_socket()
        connect_to_server(self._socket, server_host, server_port)
        logger.info(
            f"TCPClient {name} for video source {video_source.name} "
            f"initialised. Connected to {self._socket.getpeername()}"
        )

    def start_client(self) -> None:
        preprocessor = self._preprocessor
        frame_counter = 0
        for frame in self._video_source:
            if (
                self._every_nth_frame != 0
                and frame_counter % self._every_nth_frame
            ):
                frame_counter += 1
                continue

            if preprocessor:
                try:
                    frame = preprocessor(frame)
                except Exception as e:
                    logger.error(
                        f"Failed while preprocessing frame using preprocessor "
                        f"{preprocessor}. Error: {e}"
                    )
                    raise

            _, frame = cv2.imencode(
                ".jpg", frame, params=[int(cv2.IMWRITE_JPEG_QUALITY), 90]
            )
            data = pickle.dumps(frame, 0)
            size = len(data)
            try:
                self._socket.sendall(
                    struct.pack(Config.STRUCT_SIZE_FORMAT, size) + data
                )
            except Exception as e:
                logger.error(
                    f"Failed while sending frame to the server. Error: {e}"
                )
                raise
            frame_counter += 1
            logger.debug(f"Sent {frame_counter} frame to the server")
