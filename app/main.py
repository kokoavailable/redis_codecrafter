import socket
import threading
import time
import sys
import fnmatch
import os
import struct

store = {}  # 서버의 메모리 저장소
config = {}  # dir 및 dbfilename 저장

def read_length(file):
    first_byte = struct.unpack("B", file.read(1))[0]
    type_bits = first_byte >> 6  # 상위 2비트
    if type_bits == 0b00:  # 1바이트 길이
        return first_byte & 0x3F
    elif type_bits == 0b01:  # 2바이트 길이
        second_byte = struct.unpack("B", file.read(1))[0]
        return ((first_byte & 0x3F) << 8) | second_byte
    elif type_bits == 0b10:  # 5바이트 길이
        return struct.unpack(">I", file.read(4))[0]  # 4바이트 Big-endian
    else:
        raise ValueError("Unsupported length encoding")

def read_string(file):
    length = read_length(file)  # 사이즈 인코딩 처리
    return file.read(length).decode("utf-8")

def load_rdb_file():
    global config, store
    rdb_path = os.path.join(config.get("dir", "."), config.get("dbfilename", "dump.rdb"))
    
    if not os.path.exists(rdb_path):
        print(f"RDB file not found: {rdb_path}")
        return
    
    try:
        with open(rdb_path, "rb") as rdb_file:
            # Header 처리
            header = rdb_file.read(9)
            if not header.startswith(b"REDIS"):
                print("Invalid RDB file")
                return
            
            while True:
                byte = rdb_file.read(1)
                if not byte:
                    break
                
                # 메타데이터 섹션 처리
                if byte == b'\xFA':  # 메타데이터 시작
                    name = read_string(rdb_file)
                    value = read_string(rdb_file)
                    print(f"Metadata: {name} = {value}")
                    continue

                # 데이터베이스 섹션 처리
                elif byte == b'\xFE':  # 데이터베이스 섹션 시작
                    db_index = read_length(rdb_file)
                    print(f"Switching to database {db_index}")
                    continue
                
                # 해시 테이블 크기 정보 처리
                elif byte == b'\xFB':  # 해시 테이블 크기 정보
                    keys_size = read_length(rdb_file)  # 키-값 테이블 크기
                    expires_size = read_length(rdb_file)  # 만료 테이블 크기
                    print(f"Hash table sizes: keys={keys_size}, expires={expires_size}")
                    continue
                
                elif byte == b'\xFD':  # 만료 정보 (초 단위)
                    expiry = struct.unpack("<I", rdb_file.read(4))[0]
                    print(f"Key will expire at {expiry} (seconds)")
                
                elif byte == b'\xFC':  # 만료 정보 (밀리초 단위)
                    expiry = struct.unpack("<Q", rdb_file.read(8))[0]
                    print(f"Key will expire at {expiry} (milliseconds)")
                
                elif byte == b'\x00':  # 키-값 데이터 (String)
                    key = read_string(rdb_file)
                    value = read_string(rdb_file)
                    store[key] = {"value": value, "expiry": None}
                    print(f"Loaded key: {key}, value: {value}")
                
                elif byte == b'\xFF':  # 파일 끝
                    print("End of RDB file")
                    break
                
                else:
                    print(f"Unhandled byte: {byte}")
    
    except Exception as e:
        print(f"Error loading RDB file: {e}")

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
            elif cmd == "keys":
                if len(commands) < 2:
                    client_socket.sendall("-ERR Missing key or value for KEYS\r\n".encode())
                else:
                    pattern = commands[1]
                    print(pattern)
                    print(store.keys())
                    matching_keys = [key for key in store.keys() if fnmatch.fnmatch(key, pattern)]
                    print(matching_keys)
                    response = f"*{len(matching_keys)}\r\n"  # RESP 배열 시작
                    for key in matching_keys:
                        response += f"${len(key)}\r\n{key}\r\n"  # 각 키를 RESP 형식으로 추가
                    client_socket.sendall(response.encode())


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
                        expiry_time_ms = int(commands[4])
                        expiry = time.time() * 1000 + expiry_time_ms

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

    # RDB 파일 로드
    load_rdb_file()
    print(f"Initial store: {store}")

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
