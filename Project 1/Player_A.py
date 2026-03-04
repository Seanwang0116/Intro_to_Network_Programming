import socket
import time

start_port = 10001
end_port = 10011
servers = [(ip, port) for ip in ["140.113.235.151", "140.113.235.152", "140.113.235.153", "140.113.235.154"]
           for port in range(start_port, end_port + 1)]

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def find_waiting():
    waiting_players = []
    responded_players = set()
    print("正在尋找玩家...")
    for server_ip, port in servers:
        if (server_ip, port) in responded_players:
            continue 
    
        udp_socket.settimeout(0.1)
        try:
            udp_socket.sendto(b"check", (server_ip, port))
            response, addr = udp_socket.recvfrom(1024)
            if addr not in responded_players:
                print(f"收到回應: {response.decode('utf-8')} ，來自 {addr}")
                responded_players.add(addr)
                if response == b"waiting":
                    waiting_players.append(addr)
        except socket.timeout:
            print(f"無回應:  {server_ip}, port : {port}")
        except ConnectionRefusedError:
            print(f"連接被拒絕: {server_ip}, port : {port}")
        except Exception as e:
            print(f"發生錯誤: {e}")
    
    return waiting_players

def send_invitation(player):
    udp_socket.sendto(b"invite", player)
    udp_socket.settimeout(5)
    response, addr = udp_socket.recvfrom(1024)
    if response == b"accept":
        print (f"玩家 {addr} 接受邀請")
        return True
    else:
        return False

def setup_tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_ip = get_local_ip()
    tcp_socket.bind((tcp_ip, 0))
    tcp_socket.listen(5)
    tcp_port = tcp_socket.getsockname()[1]

    print(f"TCP server 建置好了, IP: {tcp_ip}, port: {tcp_port}")
    return tcp_socket, tcp_ip, tcp_port

def handle_client(conn):
    welcome_message = b"Welcome to the game!"
    conn.sendall(welcome_message)
    print(f"{welcome_message.decode('utf-8')}")
    time.sleep(0.05)
    while True:
        question = b"Paper? Scissor? Stone?: "
        conn.sendall(question)

        server_choice = input("Paper? Scissor? Stone?: ").lower()
        conn.sendall(server_choice.encode('utf-8'))
        player_choice = conn.recv(1024).decode('utf-8').lower()
        print(f"玩家A選擇: {server_choice}")
        print(f"玩家B選擇: {player_choice}")
        
        choices = ["paper", "scissor", "stone"]

        if server_choice not in choices or player_choice not in choices:
            result_message = "Unvalid choice, choose again!"
        elif player_choice == server_choice:
            result_message = "Draw! Next round!"
        elif (player_choice == "scissor" and server_choice == "paper") or \
             (player_choice == "stone" and server_choice == "scissor") or \
             (player_choice == "paper" and server_choice == "stone"):
            result_message = "PlayerB win!"
        else:
            result_message = "PlayerA Win!"
        
        time.sleep(0.1)
        conn.sendall(result_message.encode('utf-8'))
        print(f"result: {result_message}")
        if (result_message != "Unvalid choice, choose again!" and result_message != "Draw! Next round!"):
            break
        time.sleep(0.1)
    conn.close()

def send_tcp_info(udp_socket, player, message):
    udp_socket.sendto(message.encode(), player)

def display_players(waiting_players):
    print("------------------------------------------------")
    print(f"找到玩家： ")
    for idx, player in enumerate(waiting_players):
        print(f"{idx + 1}. {player}")

def choose_player(waiting_players):
    while True:
        try:
            print("------------------------------------------------")
            choice = int(input("選擇玩家：")) - 1
            if 0 <= choice < len(waiting_players):
                return waiting_players[choice]
            else:
                print("無效選擇")
        except ValueError:
            print("請輸入有效數字")

def main():
    while True:
        waiting_players = find_waiting()
        if waiting_players:
            display_players(waiting_players)
            chosen = choose_player(waiting_players)

            if send_invitation(chosen):
                tcp_socket, tcp_ip, tcp_port = setup_tcp_server()
                send_tcp_info(udp_socket, chosen, f"{tcp_ip}:{tcp_port}")
                conn, addr = tcp_socket.accept()
                handle_client(conn)
                conn.close()
                tcp_socket.close()
            else:
                print(f"玩家 {chosen} 拒絕邀請")

            print("------------------------------------------------")
            check = input("是否要繼續邀請下一位玩家？(y/n): ")
            if check.lower() != 'y':
                print("登出")
                break
        else:
            print(f"沒有玩家")
            conti = input("是否重新尋找?(y/n): ")
            if conti.lower() == 'y':
                continue
            print("登出")
            break


if __name__ == "__main__":
    main()

