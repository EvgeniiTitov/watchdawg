import socket

from watchdawg.util.logger import get_logger


logger = get_logger("communication")


def create_socket(
    family: int = socket.AF_INET, type: int = socket.SOCK_STREAM
) -> socket.socket:
    sock = socket.socket(family=family, type=type)
    logger.debug(f"Created socket of family {family}, type {type}")
    return sock


def connect_to_server(
    client_socket: socket.socket, server_host: str, server_port: int
) -> None:
    try:
        client_socket.connect((server_host, server_port))
    except Exception as e:
        logger.error(
            f"Failed to connect to server {server_host}:{server_port}. "
            f"Error: {e}"
        )
        raise e
    logger.info(f"Connected to server {server_host}:{server_port}")


def close_socket(client_socket: socket.socket) -> None:
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    logger.info("Socket closed gracefully")
