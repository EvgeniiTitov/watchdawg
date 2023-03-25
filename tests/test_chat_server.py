import socket


PORT = 9000


if __name__ == '__main__':
	tcp1 = socket.socket(socket.AF_INET , socket.SOCK_STREAM)

	tcp_ip = ""         #Any interface
	buffer_size = 1024

	tcp1.bind((tcp_ip , PORT))
	print(f"Listening on {socket.gethostname()}")

	tcp1.listen(1)
	con, addr = tcp1.accept()
	print ("TCP Connection from: ", addr)

	while True:
		data = con.recv(buffer_size).decode('utf-8')
		if not data:
			break
		print("Data received: " + data)
		print("Sending response: "  + data)
		con.send(data.encode('utf-8'))

	tcp1.close()
