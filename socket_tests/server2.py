import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((socket.gethostname(), 1234))


s.listen(5)

print("Hello")


while True:
	clientsocket, address = s.accept()
	print(f"Connection from {address} has been established!")
	message = "Welcome to the server"
	clientsocket.send(message.encode("utf-8"))
