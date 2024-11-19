import socket  # noqa: F401
import


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #

    # 포트 이미 사용중. 오류 발생
    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    client_socket, _ = server_socket.accept()
    
    while True:
        request: bytes = client_socket.recv(512)
        data: str = request.decode()

        commands = data.split("\n")
        for command in commands:
            if "ping" in command.lower():
                client_socket.sendall("+PONG\r\n".encode())
    # while True:
    #     request: bytes = client_socket.recv(512)
    #     data: str = request.decode()

    #     if "ping" in data.lower():
    #         client_socket.send("+PONG\r\n".encode())


if __name__ == "__main__":
    main()
