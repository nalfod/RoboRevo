import socket

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12345))  # Bind to localhost on port 12345
    server_socket.listen(1)  # Allow only one connection at a time

    print("Server is listening for incoming connections...")

    # Accept the connection
    conn, addr = server_socket.accept()
    print(f"Connected by {addr}")

    while True:
        data = conn.recv(1024)  # Receive up to 1024 bytes of data
        if not data:
            break
        print(f"Received from client: {data.decode()}")

        if data.decode() == 's':
            conn.sendall("They said stop!!".encode())
        # Echo the received message back to the client
        conn.sendall(data)

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
