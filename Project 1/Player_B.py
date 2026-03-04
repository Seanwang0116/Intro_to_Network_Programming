import socket

def play_game(client_socket):
    welcome = client_socket.recv(1024)
    print(f"{welcome.decode('utf-8')}")
    while True:
        question = client_socket.recv(1024).decode('utf-8')
        choice = input(f"{question}")
        client_socket.sendall(choice.encode('utf-8'))
        server_choice = client_socket.recv(1024).decode('utf-8')

        result = client_socket.recv(1024).decode('utf-8')
        print(f"玩家A選擇: {server_choice}")
        print(f"玩家B選擇: {choice}")
        print(f"result: {result}")
        if (result != "Unvalid choice, choose again!" and result != "Draw! Next round!"):
            break

def connect_to_server(server_ip, tcp_port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.settimeout(10)
    try:
        tcp_socket.connect((server_ip, tcp_port))
        print(f"已連接到 TCP server {server_ip}, port : {tcp_port}")
        return tcp_socket
    except socket.error as e:
        print(f"連接失敗: {e}")
        return None

def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('140.113.235.151', 10011))

    print("玩家 B 正在等待邀請...")

    while True:
        data, addr = udp_socket.recvfrom(1024)
        if data == b"check":
            udp_socket.sendto(b"waiting", addr)
        elif data == b"invite":
            print(f"收到來自 {addr} 的邀請")
            accept = input("接受邀請嗎？(y/n): ")
            if (accept.lower() == 'y'):
                udp_socket.sendto(b"accept", addr)
                tcp_info, addr= udp_socket.recvfrom(1024)
                try:
                    tcp_ip, tcp_port = tcp_info.decode().split(':')
                    tcp_port = int(tcp_port)
                except ValueError:
                    print(f"無法解析 TCP 資訊: {tcp_info}")
                    continue
                try:
                    client_socket = connect_to_server(tcp_ip, tcp_port)
                    if client_socket:
                        play_game(client_socket)
                except Exception as e:
                    print(f"遊戲中發生錯誤: {e}")
                client_socket.close()
                conti = input("遊戲已結束，是否繼續等待？(y/n): ")
                if (conti.lower() == 'y'):
                    print("玩家 B 正在等待邀請...")
                    continue
                else:
                    print("退出等待, 我不玩了")
                    break

            else:
                udp_socket.sendto(b"reject", addr)
                print("玩家 B 正在等待邀請...")





if __name__ == "__main__":
    start_udp_server()