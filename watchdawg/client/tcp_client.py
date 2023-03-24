from .base import BaseClient
from watchdawg.source import BaseSource
from watchdawg.util import get_logger, create_socket, connect_to_server


logger = get_logger(name="tcp_client")


class TCPClient(BaseClient):
    def __init__(
        self,
        name: str,
        video_source: BaseSource,
        server_host: str,
        server_port: int,
    ) -> None:
        super().__init__(name, video_source)
        self._socket = create_socket()
        connect_to_server(self._socket, server_host, server_port)
        logger.info(
            f"TCPClient {name} for video source {video_source.name} "
            f"initialised"
        )

    @property
    def address(self) -> str:
        return str(self._socket.getsockname())

    def start_client(self) -> None:
        # TODO: Start fetching frames from video source
        #       Pack frames and send down the socket
        #       Handle socket disconnections and errors
        for frame in self._video_source:
            pass
