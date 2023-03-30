import time

from watchdawg.backend.app import App
from watchdawg.backend.results_writer import ResultWriterMode


def main():
    app = App(mode=ResultWriterMode.SHOW_FRAMES)
    app.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        app.stop()


if __name__ == "__main__":
    main()
