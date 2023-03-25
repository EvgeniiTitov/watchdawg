from typing import Optional
import pickle
import struct

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
    ) -> None:
        super().__init__(name, video_source, frame_preprocessor)
        self._socket = create_socket()
        connect_to_server(self._socket, server_host, server_port)
        logger.info(
            f"TCPClient {name} for video source {video_source.name} "
            f"initialised. Connected to {self._socket.getpeername()}"
        )

    def start_client(self) -> None:
        preprocessor = self._preprocessor
        for frame in self._video_source:
            if preprocessor:
                try:
                    frame = preprocessor(frame)
                except Exception as e:
                    logger.error(
                        f"Failed while preprocessing frame using preprocessor "
                        f"{preprocessor}. Error: {e}"
                    )
                    raise

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
            logger.debug("Sent frame to the server")
