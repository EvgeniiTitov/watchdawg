import socket


PORT = 9000
HOST = ""


if __name__ == "__main__":
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    buffer_size = 1024

    tcp_socket.bind((HOST, PORT))

    ip = socket.gethostbyname(socket.gethostname())
    print(f"Listening on {ip}:{tcp_socket.getsockname()[1]}")

    tcp_socket.listen(1)

    while True:
        con, addr = tcp_socket.accept()
        print("TCP Connection from: ", addr)

        while True:
            data = con.recv(buffer_size).decode("utf-8")
            if not data:
                break
            print("Data received: " + data)
            print("Sending response: " + data)
            con.send(data.encode("utf-8"))

    tcp_socket.close()
