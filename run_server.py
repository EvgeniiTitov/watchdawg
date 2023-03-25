from watchdawg.server.tcp_server import TCPServer


def main():
    server = TCPServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        pass
    server.stop()


if __name__ == '__main__':
    main()
