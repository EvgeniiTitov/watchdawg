from watchdawg.client.tcp_client import TCPClient
from watchdawg.source import WebCamera
from watchdawg.preprocessor import SimplePreprocessor


def main():
    tcp_client = TCPClient(
        "Mac",
        video_source=WebCamera(),
        frame_preprocessor=SimplePreprocessor(new_width=640, flip=True),
    )
    tcp_client.start_client()


if __name__ == "__main__":
    main()
