import socket
import threading

# I am not exactly sure what this means, but this
# number should be sufficiently large 4000 < N < 10000
PORT = 5050

# first message to the server is 64 bytes long
HEADER = 64

FORMAT = "utf-8"

# on my device, this returns "marco-Aspire-V3-772"
SERVER_NAME = socket.gethostname()
# print(f"Server name: {SERVER_NAME}")

# it is possible to hard-code it
# or to search for it using the 
# socket module (this option seems prefferable)

# SERVER = "127.0.1.1"

SERVER = socket.gethostbyname(SERVER_NAME)
ADDR = (SERVER, PORT)
DISCONNECT_MESSAGE = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
	print(f"[NEW CONNECTION] {addr} connected")
	
	connected = True
	while connected:
		msg_length = conn.recv(HEADER).decode(FORMAT)
		if msg_length:
			msg_length = int(msg_length)
			msg = conn.recv(msg_length).decode(FORMAT)

			if msg == DISCONNECT_MESSAGE:
				connected = False

			print(f"[{addr}] : {msg}")
			

	conn.close()
		

def start():
	server.listen()
	print(f"[LISTENING] Server is listening on {SERVER}")
	while True:
		conn, addr = server.accept()
		thread = threading.Thread(target=handle_client, args=(conn, addr))
		thread.start()
		print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[STARTING] server is starting")
start()
