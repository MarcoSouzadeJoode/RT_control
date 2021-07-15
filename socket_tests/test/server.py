import socket

HOSTNAME = socket.gethostname()
HOST = socket.gethostbyname(HOSTNAME)

PORT = 5550


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print("Connected to", addr)
        while True:

            data_len = int(conn.recv(64))
            print(data_len)

            data = conn.recv(int(data_len))

            if not data:
                break

            print("Recieved", data.decode())

            conn.sendall("Recieved".encode())
            sent = input("> ").encode()
            conn.send(sent)