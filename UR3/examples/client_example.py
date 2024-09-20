import socket

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))  # Connect to the server on localhost and port 12345

    print("Connected to the server. Type your message:")

    while True:
        message = input("You: ")  # Get input from the user
        if message.lower() == "exit":  # Allow the client to exit by typing "exit"
            break

        client_socket.sendall(message.encode())  # Send the message to the servser

        # Receive the echoed message from the server
        data = client_socket.recv(1024)
        #print(f"Server echoed: {data.decode()}")

    client_socket.close()

if __name__ == "__main__":
    start_client()
