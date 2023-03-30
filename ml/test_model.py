from ultralytics import YOLO
import cv2


if __name__ == "__main__":
    model = YOLO(model="yolov8n.pt")

    source = cv2.VideoCapture(0)
    while True:
        has_frame, frame = source.read()
        if not has_frame:
            break

        results = model(frame)
        result_plotted = results[0].plot()

        cv2.imshow("", result_plotted)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    source.release()
    cv2.destroyAllWindows()
