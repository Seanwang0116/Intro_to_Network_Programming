import socket
import sys
import threading
import time
import traceback
import csv
import os
online_player_status = {}
room_info = {}
invitations = {}

def handle_client(client_socket):
    try:
        while True:
            q = False
            time.sleep(0.1)
            client_socket.sendall("(1) Register\n(2) Login\n(3) Quit\nChoose an option: ".encode('utf-8'))
            choice = client_socket.recv(1024).decode('utf-8')
            if choice in ['1', '2']:
                username = user_authentication(client_socket, choice)
                if username:
                    break
            elif choice == '3':
                q = True
                break
            else:
                client_socket.sendall("Invalid choice. Try again!".encode('utf-8'))
        if not q:
            handle_command(client_socket, username)
        else:
            client_socket.sendall("Goodbye!".encode('utf-8'))
    except Exception as e:
        print(f"Error handling client input: {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())

def handle_command(client_socket, username):
    while True:
        if online_player_status[username] == 'idle':
            client_socket.sendall('Input Command:\n(O)Online player List\n(L)Game List\n(R)Room List\n(C)Create Room\n(J)Join Room Management\n(I)Invitation Management\n(G)Game Develop Management\n(E)exit\nEnter a command: '.encode('utf-8'))
            command = client_socket.recv(1024).decode('utf-8').upper()
            if command == 'O':
                send_online_players(client_socket, username)
            elif command == 'L':
                send_game(client_socket)
            elif command == 'E':
                del online_player_status[username]
                broadcast_msg(f"Lobby broadcasting: Player {username} logged out.", username)
                client_socket.sendall('You have successfully logged out.'.encode('utf-8'))
                client_socket.close()
                return
            elif command == 'R':
                send_room(client_socket)
            elif command == 'C':
                create_room(client_socket, username)
            elif command == 'J':
                join_room_management(client_socket, username)
            elif command == 'I':
                invitation_management(client_socket, username)
            elif command == 'G':
                game_dev(client_socket, username)
            else:
                client_socket.sendall(f"Invalid command, try again!".encode('utf-8'))
            time.sleep(0.1)

def send_available_room(client_socket, available_rooms):
    header = f"{'Host':<15}| {'Game':<15}| {'Status':<15}"
    split = '\n--------------------------------------------------\n'
    available_table = f"{split}".join([f"{room['Host']:<15}| {room['game_type']:<15}| {room['status']}" for room in available_rooms])
    full_message = header + split + available_table

    client_socket.sendall(full_message.encode('utf-8'))
    time.sleep(0.1)

def join_room_management(client_socket, username):
    global room_info
    while True:
        available_rooms = [info for _, info in room_info.items() if (info['room_type'] == 'public' and info['status'] == 'Waiting')]

        if not available_rooms:
            client_socket.sendall('No public game rooms available.'.encode('utf-8'))
            time.sleep(0.1)
            return
        
        client_socket.sendall('Join Room Management\n(1) List available rooms\n(2) Join a room\n(3) Back to lobby\nChoose an option: '.encode('utf-8'))
        option = client_socket.recv(1024).decode('utf-8')

        if option in ['1', '2', '3']:
            if option == '1':
                send_available_room(client_socket, available_rooms)
            elif option == '2':
                if join_room(client_socket, username, available_rooms):
                    return
            elif option == '3':
                client_socket.sendall("Go back to lobby.".encode('utf-8'))
                time.sleep(0.1)
                break
        else:
            client_socket.sendall('Invalid command, try again!'.encode('utf-8'))
        time.sleep(0.1)

def join_room(client_socket, username, available_rooms):
    client_socket.sendall('Enter host name to join: '.encode('utf-8'))
    host = client_socket.recv(1024).decode('utf-8')
    match_room = None
    for room in available_rooms:
        if room['Host'] == host:
            match_room = room
            break
    
    if match_room is None:
        client_socket.sendall('Invalid command, try again!'.encode('utf-8'))
        return False
    
    if match_room['status'] == 'full' or match_room['status'] == 'In game':
        client_socket.sendall('This room is in game or full.'.encode('utf-8'))
        return False

    selected_game = match_room['game_type']
    client_socket.sendall(f'success join room@{selected_game}'.encode('utf-8'))
    time.sleep(0.1)

    send_game_to_ppl(client_socket, selected_game)
    time.sleep(0.1)

    service_in_room_player(host, client_socket, username)
    return True

def game_dev(client_socket, username):
    while True:
        client_socket.sendall('Game Develop Management\n(1) List your Games\n(2) Publish the Game\n(3) Back to the lobby\nChoose an option: '.encode('utf-8'))
        option = client_socket.recv(1024).decode('utf-8')
        if option in ['1', '2', '3']:
            if option == '1':
                client_socket.sendall('Listing your games'.encode('utf-8'))
            elif option == '2':
                client_socket.sendall('Enter your file name (ignore .py): '.encode('utf-8'))
                game_name = client_socket.recv(1024).decode('utf-8')
                client_socket.sendall(f'{game_name}'.encode('utf-8'))
                size_msg = client_socket.recv(1024).decode('utf-8')
                if 'not found' in size_msg:
                    continue
                else:
                    time.sleep(0.1)
                    file_size = int(size_msg)
                    client_socket.sendall("ACK".encode('utf-8'))

                    received_data = b""
                    while len(received_data) < file_size:
                        chunk = client_socket.recv(1024)
                        if not chunk:
                            break
                        received_data += chunk
                    file_content = received_data.decode('utf-8')
                    file_name = f'{game_name}.py'
                    file_path = os.path.join('./game_file', file_name)
                    with open(file_path, 'w') as file:
                        file.write(file_content)

                    client_socket.sendall("Introduction: ".encode('utf-8'))
                    introduction = client_socket.recv(1024).decode('utf-8')
                    save_game_info(file_name, username, introduction)
            elif option == '3':
                client_socket.sendall('Go back to lobby.'.encode('utf-8'))
                time.sleep(0.1)
                break
        else:
            client_socket.sendall('Invalid command, try again!'.encode('utf-8'))
        time.sleep(0.1)

def load_game_info():
    game_data = []
    with open('game_file/game_info.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        game_data = list(reader)
    
    return game_data

game_data = load_game_info()
def save_game_info(file_name, developer, introduction):
    global game_data
    file_name = file_name.rstrip('.py')
    game_file = 'game_file/game_info.csv'
    with open(game_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        game_data = list(reader)
    
    game_found = False
    for game in game_data:
        if game['Game Name'] == file_name:
            game['Developer'] = developer
            game['Introduction'] = introduction
            game_found = True
            break
    if not game_found:
        game_data.append({'Game Name': file_name, 'Developer': developer, 'Introduction': introduction})
     
    with open(game_file, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['Game Name', 'Developer', 'Introduction']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(game_data)

    print(f'success save game: {file_name}.')

def send_game(client_socket):
    global game_data
    if not game_data:
        full_message = 'No game available!'
    else:
        header = f"{'Game Name':<15}| {'Developer':<15}| {'Introduction':<15}"
        split = '\n--------------------------------------------------\n'
        game_table = f"{split}".join([f"{game['Game Name']:<15}| {game['Developer']:<15}| {game['Introduction']}" for game in game_data])
        full_message = header + split + game_table

    client_socket.sendall(full_message.encode('utf-8'))
    time.sleep(0.1)

def load_game_type(file_path):
    game_types = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            game_types.append(row['Game Name'])
    return game_types

def send_tcp_info(receiver_socket, ip, port):
    msg = f'{ip}:{port}'
    receiver_socket.sendall(msg.encode('utf-8'))

def start_game(client_socket, username):
    global room_info
    room = room_info[username]
    if room['status'] == 'Waiting':
        client_socket.sendall('Room is not full!'.encode('utf-8'))
        return False
    
    room['status'] = 'In game'
    player = room['joiner']
    player_socket = user_database[player]['socket']
    online_player_status[username] = 'In game'
    online_player_status[player] = 'In game'

    player_socket.sendall('game start'.encode('utf-8'))
    client_socket.sendall('game start'.encode('utf-8'))
    time.sleep(0.1)

    ip, port = room['server_ip'], room['server_port']
    send_tcp_info(player_socket, ip, port)
    return True

def service_in_room_player(host, client_socket, username):
    global room_info
    room = room_info[host]
    room['status'] = 'full'
    room['joiner'] = username
    host_socket = user_database[host]['socket']
    host_socket.sendall(f'{username} has joined the room.'.encode('utf-8'))
    online_player_status[username] = 'In room'

    while True:
        client_socket.sendall("In room... ( Role: Player )".encode('utf-8'))
        time.sleep(0.1)
        client_socket.sendall("(1) Leave the room\nChoose an option: ".encode('utf-8'))
        option = client_socket.recv(1024).decode('utf-8')

        if option == '1':
            client_socket.sendall("Go back to lobby.".encode('utf-8'))
            time.sleep(0.1)
            host_socket.sendall(f'{username} has left the room.'.encode('utf-8'))
            time.sleep(0.1)
            online_player_status[username] = 'idle'
            room['status'] = 'Waiting'
            room['joiner'] = 'Nobody'
            return
        elif option == 'Server notify: game end':
            online_player_status[username] = 'idle'
            client_socket.sendall("Go back to lobby.".encode('utf-8'))
            time.sleep(0.1)
            return
        elif option.startswith('Server notify: switch host'):
            selected_game = option.split('@')[1]
            send_game_to_ppl(client_socket, selected_game)
            service_in_room_host(client_socket, username)
            return
        else:
            client_socket.sendall("Invalid command, try again!".encode('utf-8'))
        time.sleep(0.1)

def service_in_room_host(client_socket, username):
    room = room_info[username]
    online_player_status[username] = 'In room'
    while True:
        client_socket.sendall("In room... ( Role: Host )".encode('utf-8'))
        time.sleep(0.1)
        if room['room_type'] == 'private':
            client_socket.sendall("(1) Invite player\n(2) Start game\n(3) Leave the room\nChoose an option: ".encode('utf-8'))
            option = client_socket.recv(1024).decode('utf-8')

            if option == '1':
                Invite_player(client_socket, username)
            elif option == '2':
                if start_game(client_socket, username):
                    end_msg = client_socket.recv(1024).decode('utf-8')
                    if end_msg == 'Server notify: game end':
                        destroy_room(client_socket, username)
                        client_socket.sendall("Go back to lobby.".encode('utf-8'))
                        return
            elif option == '3':
                destroy_room(client_socket, username)
                client_socket.sendall("Go back to lobby.".encode('utf-8'))
                time.sleep(0.1)
                return
            else:
                client_socket.sendall("Invalid command, try again!".encode('utf-8'))
            time.sleep(0.1)
        else:
            client_socket.sendall("(1) Start game\n(2) Leave the room\nChoose an option: ".encode('utf-8'))
            option = client_socket.recv(1024).decode('utf-8')

            if option == '1':
                if start_game(client_socket, username):
                    end_msg = client_socket.recv(1024).decode('utf-8')
                    if end_msg == 'Server notify: game end':
                        destroy_room(client_socket, username)
                        client_socket.sendall("Go back to lobby.".encode('utf-8'))
                        time.sleep(0.1)
                        return
            elif option == '2':
                destroy_room(client_socket, username)
                client_socket.sendall("Go back to lobby.".encode('utf-8'))
                time.sleep(0.1)
                return
            else:
                print(option)
                client_socket.sendall("Invalid command, try again!".encode('utf-8'))
            time.sleep(0.1)

def destroy_room(client_socket, user1):
    global room_info
    room = room_info[user1]
    player = room['joiner']
    if player != 'Nobody':
        player_socket = user_database[player]['socket']

    if room['status'] == 'Waiting':
        client_socket.sendall('Close your server'.encode('utf-8'))
        time.sleep(0.1)
    elif room['status'] == 'full':
        client_socket.sendall('Close your server'.encode('utf-8'))
        time.sleep(0.1)
        switch_control(player, player_socket, room)
    elif room['status'] == 'In game':
        online_player_status[player] = 'idle'
    
    print(f'Room for {user1} closed.')
    online_player_status[user1] = 'idle'
    del room_info[user1]

def switch_control(player, player_socket, room):
    global room_info
    player_socket.sendall('Host has leaved the room.\nYou are host now.'.encode('utf-8'))
    time.sleep(0.1)
    room_info[player] = room
    room_info[player]['Host'] = player
    room_info[player]['joiner'] = 'Nobody'
    room_info[player]['status'] = 'Waiting'
    player_socket.sendall(f"you need create room@{room_info[player]['game_type']}".encode('utf-8'))

    game_server_info = player_socket.recv(1024).decode('utf-8')
    # print(game_server_info)
    ip, port = game_server_info.split(":")
    room_info[player]['server_ip'] = ip
    room_info[player]['server_port'] = port
    print(f"Received game server info: {game_server_info}")
    print(f"Room info saved for {player}: {room_info[player]}")

def add_invitation(invitee, invitor, info):
    global invitations
    if invitee not in invitations:
        invitations[invitee] = []
    
    invitation_info = {
        'invitor': invitor,
        'message': info,
    }
    invitations[invitee].append(invitation_info)

def Invite_player(client_socket, username):
    while True:
        client_socket.sendall("Invite player\n(1) List available player\n(2) Invite player\n(3) Back to room\nChoose an option: ".encode('utf-8'))
        time.sleep(0.1)
        option = client_socket.recv(1024).decode('utf-8')
        if option == '1':
            player_list = [user for user, status in online_player_status.items() if username != user and status == 'idle']
            if not player_list:
                msg = "There is no available player!"
            else:
                msg = 'Available Players:\n' + '\n'.join(player_list)
            client_socket.sendall(msg.encode('utf-8'))
        elif option == '2':
            client_socket.sendall("Select a player to invite: ".encode('utf-8'))
            option = client_socket.recv(1024).decode('utf-8')
            player_list = [user for user, status in online_player_status.items() if username != user and status == 'idle']

            if option in player_list:
                client_socket.sendall("Invitation message: ".encode('utf-8'))
                selected_socket = user_database[option]['socket']
                invitation = client_socket.recv(1024).decode('utf-8')
                selected_socket.sendall(f'You receive new invitation from {username}, please go to invitation management page to reply.'.encode('utf-8'))
                add_invitation(option, username, invitation)
            else:
                client_socket.sendall("Invalid command, try again!".encode('utf-8'))
                time.sleep(0.1)

        elif option == '3':
            return 
        else:
            client_socket.sendall("Invalid command, try again!".encode('utf-8'))
        time.sleep(0.1)

def send_game_to_ppl(client_socket, game):
    file_path = os.path.join('game_file', f'{game}.py')
    if not os.path.exists(file_path):
        client_socket.sendall(f"Error: Game file '{game}.py' not found!".encode('utf-8'))
        return
    
    check_exist = client_socket.recv(1024).decode('utf-8')
    if check_exist == 'has exist':
        return
    
    with open(file_path, 'r') as file:
        file_content = file.read()
    file_size = len(file_content.encode('utf-8'))
    client_socket.sendall(str(file_size).encode('utf-8'))
    ack = client_socket.recv(1024).decode('utf-8')
    if ack != 'ACK':
        print("Host did not ack file size.")
        return
    
    client_socket.sendall(file_content.encode('utf-8'))
    time.sleep(0.1)

def create_room(client_socket, username):
    game_types = load_game_type('game_file/game_info.csv')
    if not game_types:
        client_socket.sendall("No game available! Go back to lobby.".encode('utf-8'))
        time.sleep(0.1)
        return
    game_type_options = "\n".join([f"({index + 1}) {game}" for index, game in enumerate(game_types)])

    client_socket.sendall(f"Select game type:\n{game_type_options}\nChoose a game: ".encode('utf-8'))
    selected_game_index = client_socket.recv(1024).decode('utf-8')
    if selected_game_index.isdigit() and 1 <= int(selected_game_index) <= len(game_types):
        selected_game_index = int(selected_game_index) - 1
    else:
        client_socket.sendall("Invalid game selection. Room creation aborted.".encode('utf-8'))
        return
    
    selected_game = game_types[selected_game_index]
    client_socket.sendall(f"You selected game type: {selected_game}".encode('utf-8'))
    time.sleep(0.1)

    room_type_message = "Select room type:\n1: Public Room\n2: Private Room\nChoose a type: "
    client_socket.sendall(room_type_message.encode('utf-8'))
    choice = client_socket.recv(1024).decode('utf-8')
    
    if choice == '1':
        client_socket.sendall("Public room created successfully!".encode('utf-8'))
        msg = f"Lobby broadcasting: {username} has create a public room." 
        broadcast_msg(msg, username)
    elif choice == '2':
        client_socket.sendall("Private room created successfully!".encode('utf-8'))
    else:
        client_socket.sendall("Invalid room type selection. Room creation aborted.".encode('utf-8'))
        return
    
    game_server_info = client_socket.recv(1024).decode('utf-8')
    ip, port = game_server_info.split(":")
    room_info[username] = {
            'Host': username,
            'joiner': 'Nobody',
            'status': 'Waiting',
            'game_type': selected_game,
            'server_ip': ip,
            'server_port': int(port),
            'room_type': 'public' if choice == '1' else 'private',
        }
    print(f"Received game server info: {game_server_info}")
    print(f"Room info saved for {username}: {room_info[username]}")

    send_game_to_ppl(client_socket, selected_game)

    service_in_room_host(client_socket, username)

def send_invitation(client_socket, username):
    global invitations
    header = f"{'Invitor':<15}| {'Room Status':<15}| {'Message'}"
    split = '\n--------------------------------------------------\n'
        
    invitation_table = []
    if username in invitations:
        for invite in invitations[username]:
            invitor = invite['invitor']
            message = invite['message']
            if invitor in room_info:
                room_status = room_info[invitor]['status']
            else:
                invitations[username] = [
                    invite for invite in invitations[username] 
                    if invite['invitor'] != invitor
                ]
                continue

            invitation_table.append(f"{invitor:<15}| {room_status:<15}| {message}")

    invitation_table_str = f'{split}'.join(invitation_table)
    msg = header + split + invitation_table_str

    client_socket.sendall(msg.encode('utf-8'))

def accept_invitation(client_socket, username):
    global invitations
    global room_info

    if not invitations.get(username):
        client_socket.sendall('There is no invitation!'.encode('utf-8'))
        return False
    
    client_socket.sendall('Enter invitor name: '.encode('utf-8'))
    invitor = client_socket.recv(1024).decode('utf-8')

    found_invitation = None
    for invite in invitations[username]:
        if invite['invitor'] == invitor:
            found_invitation = invite
            break

    if found_invitation:
        if invitor not in room_info or room_info[invitor]['status'] != 'Waiting':
            client_socket.sendall('This room is not available!'.encode('utf-8'))
            return False
        
        selected_game = room_info[invitor]['game_type']
        client_socket.sendall(f'Navigate to room...@{selected_game}'.encode('utf-8'))
        time.sleep(0.1)

        send_game_to_ppl(client_socket, selected_game)
        time.sleep(0.1)

        service_in_room_player(invitor, client_socket, username)

        invitations[username] = [
            invite for invite in invitations[username] 
            if invite['invitor'] != invitor
        ]

        return True
    else:
        client_socket.sendall("Invalid command, try again!".encode('utf-8'))
        return False

def invitation_management(client_socket, username):
    while True:
        client_socket.sendall('Invitation Management\n(1) List all the requests\n(2) Accept request\n(3) Back to the lobby\nChoose an option: '.encode('utf-8'))
        option = client_socket.recv(1024).decode('utf-8')
        if option in ['1', '2', '3']:
            if option == '1':
                send_invitation(client_socket, username)
            elif option == '2':
                if accept_invitation(client_socket, username):
                    return
            elif option == '3':
                client_socket.sendall('Go back to lobby.'.encode('utf-8'))
                time.sleep(0.1)
                break
        else:
            client_socket.sendall('Invalid command, try again!'.encode('utf-8'))
        time.sleep(0.1)

def send_online_players(client_socket, username):
    check = False
    if not online_player_status:
        msg = "No players are online."
    else:
        player_list = []
        for user, status in online_player_status.items():
            if username != user:
                player_list.append(f"{user}: {status}")
        if not player_list:
            msg = "No players are online."
        else:
            msg = 'Online Players:\n' + '\n'.join(player_list)
            check = True
    client_socket.sendall(msg.encode('utf-8'))
    time.sleep(0.1)
    return check

def send_room(client_socket):
    global room_info
    if not room_info:
        msg = "There is no game room."
    else:
        header = f"{'Host':<15}| {'Game':<15}| {'Status':<15}"
        split = '\n--------------------------------------------------\n'
        room_table = f"{split}".join([f"{room['Host']:<15}| {room['game_type']:<15}| {room['status']}" for room in room_info.values()])
        msg = header + split + room_table
        
    client_socket.sendall(msg.encode('utf-8'))
    time.sleep(0.1)

def load_user_database():
    user_database = {}
    try:
        with open('user_info.csv', mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                username = row['username']
                password = row['password']
                user_database[username] = {'password': password, 'socket': None}
    except FileNotFoundError:
        print("User database file not found. A new database will be created.")
    return user_database

def save_user_database(user_database):
    with open('user_info.csv', mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ['username', 'password']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for username, data in user_database.items():
            writer.writerow({'username': username, 'password': data['password']})

user_database = load_user_database()
def user_authentication(client_socket, choice):
    client_socket.sendall("User name: ".encode('utf-8'))
    username = client_socket.recv(1024).decode('utf-8')
    if choice == '1':   
        if username in user_database:
            client_socket.sendall("Username already exists. Please choose a different username!".encode('utf-8'))
            return None
    else:
        if username not in user_database:
            client_socket.sendall("Username does not exist. Please register first!".encode('utf-8'))
            return None
            
    client_socket.sendall("Password: ".encode('utf-8'))
    password = client_socket.recv(1024).decode('utf-8')
    
    if choice == '1':
        user_database[username] = {
            'password': password,
            'socket': client_socket,
        }
        save_user_database(user_database)
        client_socket.sendall("Registration successful! You can now log in.".encode('utf-8'))
    else:
        if user_database[username]['password'] == password:
            if username in online_player_status.keys():
                client_socket.sendall("This account has already logged in.\nChoose another one.".encode('utf-8'))
                return None
            broadcast_msg(f"Lobby broadcasting: Player {username} logged in.", username)
            time.sleep(0.1)
            client_socket.sendall("Login successful! Welcome back!".encode('utf-8'))
            user_database[username]['socket'] = client_socket
            time.sleep(0.1)
            online_player_status[username] = 'idle'
            return username
        else:
            client_socket.sendall("Incorrect password!".encode('utf-8'))
    return None

def broadcast_msg(message, username):
    print(message)

    for client_name, client_data in user_database.items():
        if client_name == username:
            continue
        if online_player_status.get(client_name) == 'idle':
            client_socket = client_data['socket']
            client_socket.sendall(message.encode('utf-8'))

def start_lobby_server(port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('140.113.235.151', port))
        server_socket.listen(10)
        print(f"Game Lobby Server started on port {port}.")
        print("Server is ready to receive player connections.")
        
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, ))
            thread.start()

    except OSError as e:
        if e.errno == 98:
            print(f"Error: Port {port} is already in use. Please try a different port.")
        else:
            print(f"Socket error occurred: {e}")
        print("Please check the error message and try restarting the server.")
        sys.exit(1)

    except Exception as e:
        print(f"Failed to start the server: {e}")
        sys.exit(1)
    finally:
        server_socket.close()

if __name__ == "__main__":
    while True:
        try:
            port = int(input("Please enter the port number to start the server: "))
            break
        except ValueError:
            print("Invalid port number. Please enter a valid integer for the port.")
    
    start_lobby_server(port)