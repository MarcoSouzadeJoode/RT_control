import socket

HOSTNAME = socket.gethostname()
HOST = socket.gethostbyname(HOSTNAME)
PORT = 7060
FORMAT = "utf-8"

HEADER = 64
ADDR = (HOST, PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(ADDR)

# f"pushing_ra_dec\n{ra}\n{dec}\n{start}\n{stop}\n{name}"
queries = ["resolve_request\nArcturus\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nFalse",
           "resolve_request\nVega\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nFalse",
           "resolve_request\nJupiter\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nTrue",
           "resolve_request\nMoon\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nTrue",
           "resolve_request\nSgr A\n2021-07-14 08:40:00\n2021-07-14 9:00:00\nFalse"]


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    s.send(send_length)
    s.send(message)


def receive(soc):
    msg_length = soc.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = soc.recv(msg_length).decode(FORMAT)
        return msg


for q in queries:
    req = q.encode()
    sent_len = str(len(req)).encode()
    message_header = sent_len + b' ' * (HEADER - len(sent_len))

    # s.send(message_header)
    # s.send(sent)
    print("[SENDING] command string: ", repr(q))
    send(q)

    msg = receive(s)

    if len(msg.split("\n")) == 6:
        info, name, ra, dec, start, stop = msg.split("\n")
        print(f"[RECEIVED] Info: {info}, RA: {ra}, DEC: {dec}, name: {name}")

        input("[USER PROMPT] waiting for user. (press enter)")
        print("[INFO] Sending back coordinates for solving.")

        command_string = f"pushing_ra_dec\n{ra}\n{dec}\n{start}\n{stop}\n{name}"
        print("[SENDING] command string: ", repr(command_string))

        send(command_string)
        converted = receive(s)
        print("[RECEIVING] ", repr(converted))
        input("[USER PROMPT] waiting for user. (press enter)")
    else:
        print(f"[RECEIVED] ", repr(msg))





