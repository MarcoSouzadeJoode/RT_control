import socket

HOSTNAME = socket.gethostname()
HOST = socket.gethostbyname(HOSTNAME)
PORT = 5550

header_size = 64

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        sent = input("> ").encode()
        sent_len = str(len(sent)).encode()
        message_header = sent_len + b' ' * (header_size - len(sent_len))

        s.send(message_header)

        s.send(sent)
        data = s.recv(1024)
        print("Recieved: ", data.decode())
