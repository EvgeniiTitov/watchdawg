import socket


def create_socket(
    family: int = socket.AF_INET, type: int = socket.SOCK_STREAM
) -> socket.socket:
    return socket.socket(family=family, type=type)
