import socket
import threading
import time
import sys

store = {}  # 서버의 메모리 저장소
config = {}  # dir 및 dbfilename 저장

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
        print(f"Error parsing Resp: {e}")

def handle_client(client_socket):
    while True:
        try:
            request: bytes = client_socket.recv(512)
            if not request:
                break
            data: str = request.decode()
            commands = parse_resp(data)

            if not commands:
                client_socket.sendall("-ERR Invalid command\r\n".encode())
                continue

            cmd = commands[0].lower()

            if cmd == 'config' and len(commands) >= 3 and commands[1].lower() == 'get':
                param = commands[2].lower()
                if param in config:
                    key = param
                    value = config[param]
                    response = (
                        f"*2\r\n"
                        f"${len(key)}\r\n{key}\r\n"
                        f"${len(value)}\r\n{value}\r\n"
                    )
                    client_socket.sendall(response.encode())
                else:
                    client_socket.sendall("*0\r\n".encode())  # RESP 빈 배열
            elif cmd == "echo":
                if len(commands) < 2:
                    client_socket.sendall("-ERR Missing argument for ECHO\r\n".encode())
                else:
                    response = f"${len(commands[1])}\r\n{commands[1]}\r\n"
                    client_socket.sendall(response.encode())
            elif cmd == "ping":
                client_socket.sendall("+PONG\r\n".encode())
            elif cmd == "set":
                if len(commands) < 3:
                    client_socket.sendall("-ERR Missing key or value for SET\r\n".encode())
                else:
                    key = commands[1]
                    value = commands[2]
                    expiry = None

                    if len(commands) > 4 and commands[3].lower() == "px":
                        expiery_time_ms = int(commands[4])
                        expiry = time.time() * 1000 + expiery_time_ms

                    store[key] = {"value": value, "expiry": expiry}
                    client_socket.sendall("+OK\r\n".encode())
            elif cmd == "get":
                if len(commands) < 2:
                    client_socket.sendall("-ERR Missing key for GET\r\n".encode())
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
    global config

    # CLI 인자로부터 dir 및 dbfilename 값을 읽음
    args = sys.argv[1:]
    for i in range(len(args)):
        if args[i] == "--dir" and i + 1 < len(args):
            config["dir"] = args[i + 1]
        elif args[i] == "--dbfilename" and i + 1 < len(args):
            config["dbfilename"] = args[i + 1]

    print(f"Loaded configuration: {config}")

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

if __name__ == "__main__":
    main()
