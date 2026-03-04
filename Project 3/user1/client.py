import importlib.util
import socket
import threading
import os
import traceback
import time
import importlib
import queue
from queue import Empty

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
    'There is no game room.',
    'Invalid game selection. Room creation aborted.',
    'Invalid room type selection. Room creation aborted.',
    'Invalid command, try again!',
    'You have successfully logged out.',
    'Go back to lobby.',
    'Invalid input. Choose a valid room number!',
    'No game available! Go back to lobby.',
    'No game available!',
]
handle_msg_in_room = [
    'Select a player to invite: ',
    'Invitation message: ',
    '(1) Start game\n(2) Leave the room\nChoose an option: ',
    '(1) Invite player\n(2) Start game\n(3) Leave the room\nChoose an option: ',
]
handle_msg_invi = [
    'Go back to lobby.',
    'There is no invitation!',
    'Invalid command, try again!',
    'This room is not available!',
]
handle_msg_join = [
    'Go back to lobby.',
    'Invalid command, try again!',
    'This room is in game or full.',
]

quit_event = threading.Event()
creator_event = threading.Event()
creator_queue = queue.Queue()
player_event = threading.Event()
player_queue = queue.Queue()

def handle_server_messages(client_socket):
    while True:
        server_msg = client_socket.recv(1024).decode('utf-8')
        if server_msg.startswith('Online') or server_msg.startswith('Game Name') or server_msg.startswith('You selected game type') or server_msg in handle_msg_in_server:
            print('--------------------------------------------------')
            print(server_msg)
            print('--------------------------------------------------')
            if server_msg == 'You have successfully logged out.':
                quit_event.set()
                break
            if server_msg.startswith('You selected game type'):
                game_type = server_msg.split(": ", 1)[1]
        elif 'Host' in server_msg and 'Game' in server_msg and 'Status' in server_msg:
            print('--------------------------------------------------')
            print(server_msg)
            print('--------------------------------------------------')
        elif server_msg in ['Public room created successfully!', 'Private room created successfully!'] or server_msg.startswith('you need create room@'):
            if not server_msg.startswith('you need create room@'):
                print('--------------------------------------------------')
                print(server_msg)
                print('--------------------------------------------------')
            else:
                game_type = server_msg.split('@')[1]
                client_socket.sendall(f'Server notify: switch host@{game_type}'.encode('utf-8'))
                time.sleep(0.1)

            tcp_socket, tcp_ip, tcp_port = setup_game_server()
            send_tcp_to_server(tcp_ip, tcp_port, client_socket)
            download_game(client_socket, game_type)
            In_room_host(tcp_socket, client_socket, game_type)
        elif server_msg.startswith('Join Room Management'):
            print(server_msg, end='', flush=True)
            join_management(client_socket)
        elif 'Lobby broadcasting: ' in server_msg or server_msg.startswith('You receive'):
            print(f'{server_msg}')
        elif server_msg.startswith('Game Develop Management'):
            print(server_msg, end='', flush=True)
            game_dev(client_socket)
        elif server_msg.startswith('Invitation Management'):
            print(server_msg, end='', flush=True)
            Invitation_management(client_socket)
        else:
            print(server_msg, end='', flush=True)

def join_management(client_socket):
    while True:
        join_msg = client_socket.recv(1024).decode('utf-8')
        if join_msg.startswith('Join Room Management'):
            print(join_msg, end='', flush=True)
        elif ('Host' in join_msg and 'Game' in join_msg and 'Status' in join_msg) or join_msg in handle_msg_join:
            print('--------------------------------------------------')
            print(join_msg)
            print('--------------------------------------------------')
            if join_msg == 'Go back to lobby.':
                return
        elif join_msg.startswith('success join room@'):
            game_type = join_msg.split('@')[1]
            download_game(client_socket, game_type)
            In_room_player(client_socket, game_type)
            return
        else:
            print(join_msg, end='', flush=True)

def In_game_invitee(ip, port, game_type):
    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    player_socket.connect((ip, port))
    print('\n--------------------------------------------------')
    print("You are in game!")
    print('--------------------------------------------------')
    player_event.set()

    game_file_path = os.path.join("game_file", f"{game_type}.py")
    download_file_path = os.path.join("download_file", f"{game_type}.py")
    
    module_path = game_file_path

    if not os.path.exists(module_path):
        module_path = download_file_path

    spec = importlib.util.spec_from_file_location(game_type, module_path)
    game_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game_module)

    msg_send = ""

    while True:
        msg_recv = player_socket.recv(1024).decode('utf-8')
        if hasattr(game_module, 'handle_msg') and any(msg in msg_recv for msg in game_module.handle_msg):
            print(msg_recv)
            continue
        elif msg_recv == 'Game end':
            break
        else:
            print(msg_recv, end='',flush=True)
        while not msg_send:
            try:
                msg_send = player_queue.get(timeout=0.1).lower()
            except Empty:
                pass

        player_socket.sendall(msg_send.encode('utf-8'))
        msg_send = ""
        
    player_event.clear()

def In_room_player(client_socket, game_type):
    while True:
        room_msg = client_socket.recv(1024).decode('utf-8')
        if room_msg == 'In room... ( Role: Player )':
            print(room_msg)
        elif room_msg == '(1) Leave the room\nChoose an option: ':
            print(room_msg, end='', flush=True)
        elif room_msg == 'game start':
            tcp_info = client_socket.recv(1024).decode('utf-8')
            ip, port = tcp_info.split(':')
            In_game_invitee(ip, int(port), game_type)
            client_socket.sendall('Server notify: game end'.encode('utf-8'))
        elif room_msg == 'Host has leaved the room.\nYou are host now.':
            print('\n--------------------------------------------------')
            print(room_msg)
            print('--------------------------------------------------')
            return
        else:
            print('--------------------------------------------------')
            print(room_msg)
            print('--------------------------------------------------')
            if room_msg == 'Go back to lobby.':
                return

def download_game(client_socket, game_type):
    file_name = f'{game_type}.py'

    check_path = os.path.join('./game_file', file_name)
    if os.path.exists(check_path):
        client_socket.sendall('has exist'.encode('utf-8'))
        return

    client_socket.sendall('ready to receive'.encode('utf-8'))
    size_msg = client_socket.recv(1024).decode('utf-8')
    file_size = int(size_msg)
    client_socket.send("ACK".encode('utf-8'))

    received_data = b""
    while len(received_data) < file_size:
        chunk = client_socket.recv(1024)
        if not chunk:
            break
        received_data += chunk
        file_content = received_data.decode('utf-8')
    file_path = os.path.join('./download_file', file_name)
    with open(file_path, 'w') as file:
        file.write(file_content)

def In_game_creator(conn, game_type):
    print('\n--------------------------------------------------')
    print("You are in game!")
    print('--------------------------------------------------')
    creator_event.set()

    game_file_path = os.path.join("game_file", f"{game_type}.py")
    download_file_path = os.path.join("download_file", f"{game_type}.py")
    
    module_path = game_file_path

    if not os.path.exists(module_path):
        module_path = download_file_path
    
    spec = importlib.util.spec_from_file_location(game_type, module_path)
    game_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game_module)

    if hasattr(game_module, 'main'):
        game_module.main(conn, creator_queue)
    
    conn.sendall('Game end'.encode('utf-8'))
    creator_event.clear()

def In_room_host(tcp_socket, client_socket, game_type):
    while True:
        server_msg = client_socket.recv(1024).decode('utf-8')
        if  server_msg.startswith('Invite player') or server_msg in handle_msg_in_room:
            print(server_msg, end='', flush=True)
        elif server_msg == 'In room... ( Role: Host )' or 'has left the room.' in server_msg or 'has joined the room.' in server_msg:
            print(server_msg)
        elif server_msg == 'game start':
            conn, addr = tcp_socket.accept()
            In_game_creator(conn, game_type)
            conn.close()
            tcp_socket.close()
            client_socket.sendall('Server notify: game end'.encode('utf-8'))
        elif server_msg == 'Close your server':
            tcp_socket.close()
        else:
            print('--------------------------------------------------')
            print(server_msg)
            print('--------------------------------------------------')
            if server_msg == 'Go back to lobby.':
                return

def Invitation_management(client_socket):
    while True:
        Invi_msg = client_socket.recv(1024).decode('utf-8')
        if Invi_msg.startswith('Invitation Management'):
            print(Invi_msg, end='', flush=True)
        elif ('Invitor' in Invi_msg and 'Room Status' in Invi_msg) or Invi_msg in handle_msg_invi:
            print('--------------------------------------------------')
            print(Invi_msg)
            print('--------------------------------------------------')
            if Invi_msg == 'Go back to lobby.':
                return
        elif Invi_msg.startswith('Navigate to room...'):
            msg, game_type = Invi_msg.split('@')
            print(msg)
            download_game(client_socket, game_type)
            In_room_player(client_socket, game_type)
            return
        else:
            print(Invi_msg, end='', flush=True)

def game_dev(client_socket):
    game_folder = './game_file'
    while True:
        game_msg = client_socket.recv(1024).decode('utf-8')
        if game_msg.startswith('Game Develop Management'):
            print(game_msg, end='', flush=True)
        elif game_msg.startswith('Listing'):
            game_files = [os.path.splitext(file)[0] 
                for file in os.listdir(game_folder) 
                if file.endswith('.py')
            ]
            if game_files:
                files_list = '\n'.join(f'({i + 1}) {file}' for i, file in enumerate(game_files))
                print('--------------------------------------------------')
                print(files_list)
                print('--------------------------------------------------')
            else:
                print('--------------------------------------------------')
                print('No games found in the folder.')
                print('--------------------------------------------------')
        elif game_msg.startswith('Enter your file name'):
            print(game_msg, end='', flush=True)
            file_name = client_socket.recv(1024).decode('utf-8')
            file_path = os.path.join(game_folder, f"{file_name}.py")
            send_game_to_server(client_socket, file_name, file_path)
        elif game_msg == 'Go back to lobby.':
            print('--------------------------------------------------')
            print(game_msg)
            print('--------------------------------------------------')
            break
        else:
            print(game_msg)

def send_game_to_server(client_socket, file_name, file_path):
    if not os.path.exists(file_path):
        client_socket.send(f"File '{file_name}.py' not found.".encode('utf-8'))
        print(f"Public Error: file not found")
        return
    
    with open(file_path, 'r') as file:
        file_content = file.read()
    file_size = len(file_content.encode('utf-8'))
    client_socket.send(str(file_size).encode('utf-8'))
    ack = client_socket.recv(1024).decode('utf-8')
    if ack != 'ACK':
        print("Server did not ack file size.")
        return
    client_socket.sendall(file_content.encode('utf-8'))

    intro_msg = client_socket.recv(1024).decode('utf-8')
    print(intro_msg, end='', flush=True)

def send_tcp_to_server(tcp_ip, tcp_port, client_socket):
    game_server_info = f"{tcp_ip}:{tcp_port}"
    client_socket.send(game_server_info.encode('utf-8'))
    # print(f"Sent game server info to lobby: {game_server_info}")
    time.sleep(0.1)

def setup_game_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_ip = '140.113.235.151'
    tcp_socket.bind((tcp_ip, 0))
    tcp_socket.listen(2)
    tcp_port = tcp_socket.getsockname()[1]

    # print(f"TCP server 建置好了, IP: {tcp_ip}, port: {tcp_port}")
    return tcp_socket, tcp_ip, tcp_port

def In_server(client_socket, init_host, init_port):
    quit_event.clear()
    creator_event.clear()
    player_event.clear()
    listen_thread = threading.Thread(target=handle_server_messages, args=(client_socket,))
    listen_thread.daemon = True
    listen_thread.start()

    while not quit_event.is_set():
        msg_send = input()
        if creator_event.is_set():
            creator_queue.put(msg_send)
            continue
        if player_event.is_set():
            player_queue.put(msg_send)
            continue
        client_socket.send(msg_send.encode('utf-8'))
        if msg_send in ['e', 'E']:
            break

    connect_to_server(init_host, init_port)

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print("Connected to the game lobby server.")
        while True:
            quit = False
            server_msg = client_socket.recv(4096).decode('utf-8')
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
        traceback.print_exc()

if __name__ == "__main__":
    host = '140.113.235.151'
    while True:
        try:
            port = int(input("Please enter the port number to start the server: "))
            break
        except ValueError:
            print("Invalid port number. Please enter a valid integer for the port.")
    connect_to_server(host, port)