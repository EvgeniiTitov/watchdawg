import socket


PORT = 9000
SERVER_HOST = ""


if __name__ == '__main__':
	tcp1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	buffer_size = 1024
	msg = ("Client test.")

	tcp1.connect((SERVER_HOST, PORT))
	print("Sending message: " + msg)
	tcp1.send(msg.encode('utf8'))

	data = tcp1.recv(buffer_size).decode('utf-8')
	print("Data reveived: " + data)
