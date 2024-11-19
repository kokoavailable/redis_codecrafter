import socket  # noqa: F401
import threading

def parse_resp(data):
    lines = data.split("\r\n")
    if lines[0].startswith("*"):
        num_elements = int(lines[0][1:])
        elements = []
        for i in range(num_elements):
            element = lines[2 * i + 2]
            elements.append(element)
        return elements
    return []

def handle_client(client_socket):
    request = client_socket.recv(512).decode().strip()
    command = parse_resp(request)  # RESP 프로토콜 파싱 시도

    if not command:  # RESP 형식이 아니면 단순 명령으로 처리
        command = [request]

    if command[0].lower() == "echo":
        if len(command) < 2:
            client_socket.sendall("-ERR Missing argument for ECHO\r\n".encode())
        else:
            response = f"${len(command[1])}\r\n{command[1]}\r\n"
            client_socket.sendall(response.encode())
    elif command[0].lower() == "ping":
        client_socket.sendall("+PONG\r\n".encode())
    else:
        client_socket.sendall("-ERR Unknown command\r\n".encode())
    # while True:
    #     try:
    #         request:bytes = client_socket.recv(512)
    #         if not request:
    #             break
    #         data: str = request.decode()

    #         commands = data.split("\n")
    #         for command in commands:
    #             if "ping" in command.lower():
    #                 client_socket.sendall("+PONG\r\n".encode())
    #     except Exception as e:
    #         print(f"Error handling client: {e}")
    #         break
    # client_socket.close()

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #

    # 포트 이미 사용중. 오류 발생
    try:
        server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
        
        while True:
            client_socket, _ = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()

    except Exception as e:
        print(f"Server error: {e}")
    # while True:
    #     request: bytes = client_socket.recv(512)
    #     data: str = request.decode()

    #     if "ping" in data.lower():
    #         client_socket.send("+PONG\r\n".encode())


if __name__ == "__main__":

    main()
