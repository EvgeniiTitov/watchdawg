from watchdawg.client.tcp_client import TCPClient
from watchdawg.source import WebCamera
from watchdawg.client.preprocessor import Resizer
from watchdawg.util.decorators import measure_peak_ram
from watchdawg.config import Config


@measure_peak_ram
def main():
    source = WebCamera()
    preprocessor = Resizer(
        new_width=Config.MODEL_INPUT_WIDTH,
        new_height=Config.MODEL_INPUT_HEIGHT,
        flip=True,
    )
    try:
        tcp_client = TCPClient(
            "Mac",
            video_source=source,
            frame_preprocessor=preprocessor,
        )
        tcp_client.start_client()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
