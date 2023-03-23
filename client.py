import io
import socket
import struct

import cv2
import numpy as np


class Camera:
    def __init__(self) -> None:
        self._cap = cv2.VideoCapture(0)

    def __iter__(self) -> np.ndarray:
        while True:
            has_frame, frame = self._cap.read()
            if not has_frame:
                break
            yield frame

    def close(self) -> None:
        self._cap.release()


def main() -> None:
    camera = Camera()
    try:
        for frame in camera:
            cv2.imshow("", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        print("Stopped")
    camera.close()


if __name__ == '__main__':
    main()
