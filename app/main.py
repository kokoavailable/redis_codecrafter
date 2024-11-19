import socket  # noqa: F401
import threading
import time

store = {}

def parse_resp(data):
    try:
        lines = data.split("\r\n")
        if lines[0].startswith("*"):
            num_elements = int(lines[0][1:])
            elements = []
            for i in range(num_elements):
                element = lines[2 * i + 2]
                elements.append(element)
            return elements
        elif lines[0].lower() == 'ping':
            return ['ping']

    except Exception as e:
        print(f"Error parsing Resp:{e}")

def handle_expiry():
    while True:
        current_time = time.time() * 1000
        keys_to_delete = []
        for key, meta in store.items():
            if meta.get("expiry") < current_time:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del store[key]
        time.sleep(0.1)

def handle_client(client_socket):
    while True:
        try:
            request: bytes = client_socket.recv(512)
            if not request:
                break
            data: str = request.decode()
            commands = parse_resp(data)

            if commands[0].lower() == 'echo':
                if len(commands) < 2:
                    client_socket.sendall("-ERR Missing argument for ECHO\r\n".encode())
                else:
                    response = f"${len(commands[1])}\r\n{commands[1]}\r\n"
                    client_socket.sendall(response.encode())
            elif commands[0].lower() == "ping":
                client_socket.sendall("+PONG\r\n".encode())
            elif commands[0].lower() == "set":
                if len(commands) < 3:
                    client_socket.sendall("-ERR Missing key or value for SET\r\n")
                else:
                    key = commands[1]
                    value = commands[2]
                    expiry = None

                    if len(commands) > 4 and commands[3].lower() == "px":
                        expiery_time_ms = int(commands[4])
                        expiry = time.time() * 1000 + expiery_time_ms

                    store[key] = {"value": value, "expiry":expiry}
                    client_socket.sendall("+OK\r\n".encode())
            elif commands[0].lower() == "get":
                if len(commands) < 2:
                    client_socket.sendall("-ERR Missing key for GET\r\n")
                else:
                    key = commands[1]
                    meta = store.get(key)
                    if not meta:
                        client_socket.sendall("$-1\r\n".encode())
                    else:
                        expiry = meta.get("expiry")
                        if expiry and expiry < time.time() * 1000:
                            del store[key]
                            client_socket.sendall("$-1\r\n".encode())
                        else:
                            value = meta["value"]
                            response = f"${len(value)}\r\n{value}\r\n"
                            client_socket.sendall(response.encode())

            else:
                client_socket.sendall("-ERR Unknown command\r\n".encode())


        except Exception as e:
            print(f"Error handling client: {e}")
            break
    client_socket.close()

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
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket,)
            )
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