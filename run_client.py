from watchdawg.client.tcp_client import TCPClient
from watchdawg.source import WebCamera


def main():
    webcam_source = WebCamera()
    tcp_client = TCPClient("WorkMac", video_source=webcam_source)
    tcp_client.start_client()


if __name__ == "__main__":
    main()
