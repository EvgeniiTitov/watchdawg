from watchdawg.client.tcp_client import TCPClient
from watchdawg.source import WebCamera
from watchdawg.preprocessor import Resizer


def main():
    tcp_client = TCPClient(
        "Mac",
        video_source=WebCamera(),
        frame_preprocessor=Resizer(new_width=320)
    )
    tcp_client.start_client()


if __name__ == "__main__":
    main()
