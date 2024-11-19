import socket
import threading
def handle_client(client_socket, client_address):
    while True:
        request = client_socket.recv(1024)
        data = request.decode()
        # data = "*2\r\n$4\r\necho\r\n$3\r\nhey\r\n"
        response = "+PONG\r\n"
        if "echo" in data:
            res_data = data.split("\r\n")[-2]
            content_len = len(res_data)
            response = f"${content_len}\r\n{res_data}\r\n"
        client_socket.send(response.encode())
def main():
    print("Logs from your program will appear here!")
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address[0]}:{client_address[1]}")
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket, client_address)
        )
        client_thread.start()
if __name__ == "__main__":
    main()