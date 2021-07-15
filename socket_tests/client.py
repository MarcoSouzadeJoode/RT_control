import socket

HEADER = 64
PORT = 7070
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER_NAME = socket.gethostname()
SERVER = socket.gethostbyname(SERVER_NAME)
ADDR = (SERVER, PORT)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

	def send(msg):
		message = msg.encode(FORMAT)
		msg_length = len(message)
		send_length = str(msg_length).encode(FORMAT)
		send_length += b' ' * (HEADER - len(send_length))
		s.send(send_length)
		s.send(message)

	s.connect((SERVER, PORT))

	print("resolve_request\nArcturus\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nFalse")
	send("resolve_request\nArcturus\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nFalse")
	print("pushing_ra_dec\n280\n38\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nVega")

	send("pushing_ra_dec\n280\n38\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nVega")

	send("!DISCONNECT")



