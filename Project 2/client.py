import socket
import game_1
import game_2
handle_msg_connect = [
    'Invalid choice. Try again!',
    'Registration successful! You can now log in.',
    'Username already exists. Please choose a different username!',
    'Username does not exist. Please register first!',
    'Incorrect password!',
    'This account has already logged in.\nChoose another one.',
    'Goodbye!',
]
handle_msg_in_server = [
    'No players are online.',
    'No public game rooms available.',
    'Invalid game selection. Room creation aborted.',
    'Invalid room type selection. Room creation aborted.',
    'Invalid command, try again!',
    'You have successfully logged out.',
    'Go back to lobby.',
    'The room is full. Choose another room!',
    'Invalid input. Choose a valid room number!',
    'Error: Logout failed due to server issue. Please try again.',
]

handle_msg_in_room = [
    'Invalid game selection. Room creation aborted.',
    'Invalid room type selection. Room creation aborted.',
    'Go back to lobby.',
]

handle_msg_in_game_A = [
    'Invalid choice, choose again!',
    'Draw! Next round!',
    "You Win!",
    "You Lose!",
]

handle_msg_in_game_B = [
    'This cell has already taken, choose another!',
    'Invalid choose, try again!',
    "You Win!",
    "You Lose!",
    "Draw!",
    'Waiting...',
]

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print("Connected to the game lobby server.")
        while True:
            quit = False
            server_msg = client_socket.recv(4096).decode('utf-8')
            if server_msg.startswith('      '):
                print(server_msg)
                continue
            if server_msg in handle_msg_connect:
                print(server_msg)
                if server_msg == 'Goodbye!':
                    quit = True
                    break
                continue
            if server_msg == 'Login successful! Welcome back!':
                print('--------------------------------------------------')
                print(server_msg)
                print('--------------------------------------------------')
                break
            msg_send = input(server_msg)
            client_socket.send(msg_send.encode('utf-8'))
        if not quit:
            In_server(client_socket, host, port)
    except Exception as e:
        print(f"{e}")

def handle_invitation(server_msg, client_socket):
    print('--------------------------------------------------')
    print('Invitation!!!')
    print(server_msg, end='')
    while True:
        try:
            choose = input().lower()
            if choose not in ['y', 'n']:
                print('Invalid input. Please enter y or n: ', end='')
                continue
            client_socket.sendall(choose.encode('utf-8'))
            if choose == 'y':
                tcp_info = client_socket.recv(1024).decode('utf-8')
                # print(tcp_info)
                ip, port = tcp_info.split(':')
                In_game_invitee(ip, int(port))
            break
            
        except Exception as e:
            print(f"Error handling invitation: {e}")

def In_server(client_socket, init_host, init_port):
    while True:
        server_msg = client_socket.recv(1024).decode('utf-8')
        if server_msg.startswith('Online') or server_msg.startswith('You selected game type') or server_msg in handle_msg_in_server or server_msg.startswith('Public Game Rooms:'):
            game_type = 'Pape, Scissor, Stone' if 'Pape, Scissor, Stone' in server_msg else 'OOXX' 
            print('--------------------------------------------------') 
            print(server_msg)
            print('--------------------------------------------------')
            if server_msg == 'You have successfully logged out.':
                break
            continue
        elif server_msg in ['Public room created successfully!', 'Private room created successfully!']:
            print('--------------------------------------------------')
            print(server_msg)
            print('--------------------------------------------------')
            tcp_socket, tcp_ip, tcp_port = setup_game_server()
            send_tcp_to_server(tcp_ip, tcp_port, client_socket)
            In_room(tcp_socket, client_socket, game_type)
            
        elif server_msg.startswith('You have been'):
            handle_invitation(server_msg, client_socket)
        elif server_msg == 'success join room':
            tcp_info = client_socket.recv(1024).decode('utf-8')
            # print(tcp_info)
            ip, port = tcp_info.split(':')
            In_game_invitee(ip, int(port))
        else:
            msg_send = input(server_msg)
            client_socket.send(msg_send.encode('utf-8'))

    connect_to_server(init_host, init_port)

def send_tcp_to_server(tcp_ip, tcp_port, client_socket):
    game_server_info = f"{tcp_ip}:{tcp_port}"
    client_socket.send(game_server_info.encode('utf-8'))
    # print(f"Sent game server info to lobby: {game_server_info}")

def setup_game_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_ip = '140.113.235.151'
    tcp_socket.bind((tcp_ip, 0))
    tcp_socket.listen(2)
    tcp_port = tcp_socket.getsockname()[1]

    # print(f"TCP server 建置好了, IP: {tcp_ip}, port: {tcp_port}")
    return tcp_socket, tcp_ip, tcp_port

def In_game_invitee(ip, port):
    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    player_socket.connect((ip, port))
    print('--------------------------------------------------')
    print("You are in game!")
    print('--------------------------------------------------')

    while True:
        msg_recv = player_socket.recv(1024).decode('utf-8')
        if msg_recv.startswith('You choose:') or msg_recv.startswith('Your opponent choose:') or msg_recv in handle_msg_in_game_A:
            print(msg_recv)
            continue
        elif msg_recv in handle_msg_in_game_B or '---+---+---' in msg_recv:
            print(msg_recv)
            continue
        if msg_recv == 'Game end':
            print('--------------------------------------------------')
            print(msg_recv)
            print('--------------------------------------------------')
            break

        msg_send = input(msg_recv)
        player_socket.send(msg_send.encode('utf-8'))
    

def In_game_creator(conn, game_type):
    print('--------------------------------------------------')
    print("You are in game!")
    print('--------------------------------------------------')
    if game_type == 'Pape, Scissor, Stone':
        game_1.main(conn)
    else:
        game_2.main(conn)

    conn.sendall('Game end'.encode('utf-8'))
    print('--------------------------------------------------')
    print("Game end")
    print('--------------------------------------------------')

def In_room(tcp_socket, client_socket, game_type):
    while True:
        server_msg = client_socket.recv(1024).decode('utf-8')
        if server_msg.startswith('Online') or server_msg in handle_msg_in_server:
            print('--------------------------------------------------') 
            print(server_msg)
            print('--------------------------------------------------')
            if server_msg in handle_msg_in_room:
                if tcp_socket:
                    tcp_socket.close()
                break
            continue
        elif server_msg.startswith('Waiting') or 'reject' in server_msg:
            print('--------------------------------------------------')
            print(server_msg)
            print('--------------------------------------------------')
            continue
        elif server_msg == 'Game start' or 'accept' in server_msg:
            if 'accept' in server_msg:
                print('--------------------------------------------------')
                print(server_msg)
                print('--------------------------------------------------')
            conn, addr = tcp_socket.accept()
            In_game_creator(conn, game_type)
            conn.close()
            tcp_socket.close()
            client_socket.sendall('Game end'.encode('utf-8'))
            break
        elif  server_msg.startswith('You have been'):
            handle_invitation(server_msg, client_socket)
            break
        msg_send = input(server_msg)
        client_socket.send(msg_send.encode('utf-8'))

if __name__ == "__main__":
    host = '140.113.235.151'
    while True:
        try:
            port = int(input("Please enter the port number to start the server: "))
            break
        except ValueError:
            print("Invalid port number. Please enter a valid integer for the port.")
    connect_to_server(host, port)
