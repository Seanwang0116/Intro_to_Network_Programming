import socket
import sys
import threading
import time
import traceback
def game_lobby():
    lobby = """        ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄       ▄▄  ▄▄▄▄▄▄▄▄▄▄▄ 
       ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░▌     ▐░░▌▐░░░░░░░░░░░▌
       ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀█░▌▐░▌░▌   ▐░▐░▌▐░█▀▀▀▀▀▀▀▀▀ 
       ▐░▌          ▐░▌       ▐░▌▐░▌▐░▌ ▐░▌▐░▌▐░▌          
       ▐░▌ ▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌▐░▌ ▐░▐░▌ ▐░▌▐░█▄▄▄▄▄▄▄▄▄ 
       ▐░▌▐░░░░░░░░▌▐░░░░░░░░░░░▌▐░▌  ▐░▌  ▐░▌▐░░░░░░░░░░░▌
       ▐░▌ ▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░▌   ▀   ▐░▌▐░█▀▀▀▀▀▀▀▀▀ 
       ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌          
       ▐░█▄▄▄▄▄▄▄█░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░█▄▄▄▄▄▄▄▄▄ 
       ▐░░░░░░░░░░░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░░░░░░░░░░░▌
        ▀▀▀▀▀▀▀▀▀▀▀  ▀         ▀  ▀         ▀  ▀▀▀▀▀▀▀▀▀▀▀ 

 ▄▄           ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄   ▄▄▄▄▄▄▄▄▄▄   ▄         ▄ 
▐░░▌         ▐░░░░░░░░░░░▌▐░░░░░░░░░░▌ ▐░░░░░░░░░░▌ ▐░▌       ▐░▌
▐░░▌         ▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░▌       ▐░▌
▐░░▌         ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌
▐░░▌         ▐░▌       ▐░▌▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌
▐░░▌         ▐░▌       ▐░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
▐░░▌         ▐░▌       ▐░▌▐░█▀▀▀▀▀▀▀█▌ ▐░█▀▀▀▀▀▀▀█▌  ▀▀▀▀█░█▀▀▀▀ 
▐░░▌         ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌     ▐░▌     
▐░░█▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌     ▐░▌     
▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌     ▐░▌     
 ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀   ▀▀▀▀▀▀▀▀▀▀        ▀      
"""
    return lobby

user_database = {}
online_player_status = {}
room_info = {}
inviting = {}
blocking = {}
def handle_client(client_socket):
    try:
        while True:
            q = False
            time.sleep(0.01)
            client_socket.sendall("Register or Login or Quit: ".encode('utf-8'))
            choice = client_socket.recv(1024).decode('utf-8').lower()
            if choice in ['register', 'login']:
                username = user_authentication(client_socket, choice)
                if username:
                    break
            elif choice == 'quit':
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
            client_socket.sendall('Input Command:\nOnline player list(O)\nRoom list(R)\nCreate room(C)\nJoin room(J)\nexit(E)): '.encode('utf-8'))
            command = client_socket.recv(1024).decode('utf-8').upper()
            blocking[username] = False
            if username in inviting.keys():
                continue
            if command == 'O':
                send_online_players(client_socket, username)
            elif command == 'E':
                if log_out(client_socket, username):
                    client_socket.sendall('You have successfully logged out.'.encode('utf-8'))
                    client_socket.close()
                else:
                    client_socket.sendall('Logout failed. Would you like to retry? (Y/N): '.encode('utf-8'))
                    retry_command = client_socket.recv(1024).decode('utf-8').upper()
                    if retry_command != 'Y':
                        client_socket.sendall('Exiting without logout. Goodbye!'.encode('utf-8'))
                        continue
                break
            elif command == 'R':
                send_public_room(client_socket)
            elif command == 'C':
                create_room(client_socket, username)
            elif command == 'J':
                join_room(client_socket, username)
            else:
                client_socket.sendall(f"Invalid command, try again!".encode('utf-8'))
                time.sleep(0.001)

def service_in_room(client_socket, username):
    room = room_info[username]
    In_game = False
    if room['room_type'] == 'private':
        while not In_game:
            check = send_online_players(client_socket, username)
            time.sleep(0.01)
            if not check:
                client_socket.sendall(
                    "Choose an option:\n1. Type 'r' to refresh online player list 2. Type 'q' to quit the room: ".encode('utf-8')
                )
                choice = client_socket.recv(1024).decode('utf-8').lower()
                if choice == 'r':
                    continue
                elif choice == 'q':
                    destroy_room(client_socket, username, None, None)
                    break
                else:
                    client_socket.sendall("Invalid command, try again!".encode('utf-8'))
                    time.sleep(0.001)
            else:
                client_socket.sendall("Choose a player to invite: ".encode('utf-8'))
                choose = client_socket.recv(1024).decode('utf-8')
                if choose in online_player_status and online_player_status[choose] == 'idle' and choose != username:
                    receiver_socket = user_database[choose]['socket']
                    inviting[choose] = username
                    online_player_status[choose] = 'Busy'
                    if send_invitation(client_socket, username, receiver_socket, choose):
                        In_game = True
                        break
                else:
                    client_socket.sendall("Invalid command, try again!".encode('utf-8'))
                    time.sleep(0.001)
       
    else:
        client_socket.sendall("Waiting...".encode('utf-8'))
        while room_info[username]['joiner'] == 'Nobody':
            time.sleep(0.5)
        choose = room_info[username]['joiner']
        receiver_socket = user_database[choose]['socket']
        In_game = True
        client_socket.sendall('Game start'.encode('utf-8'))
        
    if In_game:
        handle_in_game(client_socket, username, receiver_socket, choose)
            

def handle_in_game(client_socket, user1, receiver_socket, user2):
    room = room_info[user1]
    room['status'] = 'In game'
    ip, port = room['server_ip'], room['server_port']
    send_tcp_info(receiver_socket, ip, port)

    online_player_status[user1], online_player_status[user2] = 'In game', 'In game'

    end_msg = client_socket.recv(1024).decode('utf-8')
    if end_msg == 'Game end':
        destroy_room(client_socket, user1, receiver_socket, user2)
    
    if user2 in inviting:
        del inviting[user2]
        online_player_status[user2] = 'idle'

def send_invitation(client_socket, sender, receiver_socket, receiver):
    client_socket.sendall(f'Waiting {receiver} to response...'.encode('utf-8'))

    invite_msg = (f"You have been invited to a game room created by {sender}.\n"
        "Do you want to join(y/n): ")
    receiver_socket.sendall(invite_msg.encode('utf-8'))
    blocking[receiver] = True
    while blocking[receiver]:
        time.sleep(1)

    msg = receiver_socket.recv(1024).decode('utf-8')
    if msg == 'y':
        client_socket.sendall(f"{receiver} accept the invitation!".encode('utf-8'))
        return True
    
    client_socket.sendall(f"Player {receiver} reject the invitation!".encode('utf-8'))
    time.sleep(0.001)
    online_player_status[receiver] = 'idle'
    del inviting[receiver]
    return False

def send_tcp_info(receiver_socket, ip, port):
    msg = f'{ip}:{port}'
    receiver_socket.sendall(msg.encode('utf-8'))
    # print('send success')

def destroy_room(client_socket, user1, receiver_socket, user2):
    msg = "Go back to lobby."
    client_socket.sendall(msg.encode('utf-8'))

    if receiver_socket:
        receiver_socket.sendall(msg.encode('utf-8'))

    time.sleep(0.001)
    del room_info[user1]
    print(f"Game room for {user1} closed.")
    
    online_player_status[user1] = 'idle'
    if user2 != None:
        online_player_status[user2] = 'idle'
        if user2 in inviting:
            del inviting[user2]

def join_room(client_socket, username):
    public_rooms = send_public_room(client_socket)
    time.sleep(0.001)
    if public_rooms:
        while True:
            msg = 'Choose a room to join: '
            client_socket.sendall(msg.encode('utf-8'))
        
            choose = client_socket.recv(1024).decode('utf-8')
            
            if choose.isdigit() and 1 <= int(choose) <= len(public_rooms):
                selected_room = public_rooms[int(choose) - 1]
                
                if selected_room['status'] == 'In game':
                    public_rooms = send_public_room(client_socket)
                    time.sleep(0.001)
                    error_msg = 'The room is full. Choose another room!'
                    client_socket.sendall(error_msg.encode('utf-8'))
                    time.sleep(0.001)
                else:
                    break
            else:
                error_msg = 'Invalid input. Choose a valid room number!'
                client_socket.sendall(error_msg.encode('utf-8'))
                time.sleep(0.001)
        
        client_socket.sendall('success join room'.encode('utf-8'))
        time.sleep(0.001)
        creator = selected_room['creator']
        room_info[creator]['joiner'] = username
        online_player_status[username] = 'In game'
    else:
        return

def create_room(client_socket, username):
    game_type = ['Pape, Scissor, Stone', 'OOXX']
    game_type_options = "\n".join([f"{index + 1}: {game}" for index, game in enumerate(game_type)])

    client_socket.sendall(f"Select game type:\n{game_type_options}\nChoose (1-2): ".encode('utf-8'))
    selected_game_index = client_socket.recv(1024).decode('utf-8')
    if selected_game_index.isdigit() and 1 <= int(selected_game_index) <= 2:
        selected_game_index = int(selected_game_index) - 1
    else:
        if username not in inviting:
            client_socket.sendall("Invalid game selection. Room creation aborted.".encode('utf-8'))
        return
    
    selected_game = game_type[selected_game_index]
    client_socket.sendall(f"You selected game type: {selected_game}".encode('utf-8'))
    time.sleep(0.001)

    room_type_message = "Select room type:\n1: Public Room\n2: Private Room\nChoose (1-2): "
    client_socket.sendall(room_type_message.encode('utf-8'))
    choice = client_socket.recv(1024).decode('utf-8')
    
    if choice == '1':
        client_socket.sendall(f"Public room created successfully!".encode('utf-8'))
    elif choice == '2':
        client_socket.sendall(f"Private room created successfully!".encode('utf-8'))
    else:
        if username not in inviting:
            client_socket.sendall("Invalid room type selection. Room creation aborted.".encode('utf-8'))
        return
    
    game_server_info = client_socket.recv(1024).decode('utf-8')
    ip, port = game_server_info.split(":")
    room_info[username] = {
            'creator': username,
            'joiner': 'Nobody',
            'status': 'idle',
            'game_type': selected_game,
            'server_ip': ip,
            'server_port': int(port),
            'room_type': 'public' if choice == '1' else 'private',
        }
    print(f"Received game server info: {game_server_info}")
    print(f"Room info saved for {username}: {room_info[username]}")
    service_in_room(client_socket, username)

def log_out(client_socket, username):
    try:
        del online_player_status[username]
        if username in inviting:
            del inviting[username]
        print(f"Player {username} logged out.")
        return True
    except Exception as e:
        print(f"Error logging out player {username}: {e}")
        client_socket.sendall("Error: Logout failed due to server issue. Please try again.".encode('utf-8'))
        return False

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
    time.sleep(0.001)
    return check

def send_public_room(client_socket):
    public_rooms = [info for _, info in room_info.items() if info['room_type'] == 'public']
    if not public_rooms:
        msg = "No public game rooms available."
    else:
        msg = "Public Game Rooms:\n"
        for idx, room in enumerate(public_rooms, start=1):
            msg += (f"{idx}. Creator: {room['creator']}, Game Type: {room['game_type']}, Status: {room['status']}\n")
        msg =  msg.rstrip('\n')

    time.sleep(0.01)
    client_socket.sendall(msg.encode('utf-8'))
    time.sleep(0.01)
    return public_rooms

def user_authentication(client_socket, choice):
    client_socket.sendall("User name: ".encode('utf-8'))
    username = client_socket.recv(1024).decode('utf-8')
    if choice == 'register':   
        if username in user_database:
            client_socket.sendall("Username already exists. Please choose a different username!".encode('utf-8'))
            return None
    else :
        if username not in user_database:
            client_socket.sendall("Username does not exist. Please register first!".encode('utf-8'))
            return None
            
    client_socket.sendall("Password: ".encode('utf-8'))
    password = client_socket.recv(1024).decode('utf-8')
    
    if choice == 'register':
        user_database[username] = {
            'password': password,
            'socket': client_socket,
        }
        client_socket.sendall("Registration successful! You can now log in.".encode('utf-8'))
    else:
        if user_database[username]['password'] == password:
            if username in online_player_status.keys():
                client_socket.sendall("This account has already logged in.\nChoose another one.".encode('utf-8'))
                return None
            print(f"Player {username} logged in.")
            lobby = game_lobby()
            client_socket.sendall(lobby.encode('utf-8'))
            time.sleep(0.01)
            client_socket.sendall("Login successful! Welcome back!".encode('utf-8'))
            user_database[username]['socket'] = client_socket
            time.sleep(0.01)
            send_online_players(client_socket, username)
            send_public_room(client_socket)
            online_player_status[username] = 'idle'
            return username
        else:
            client_socket.sendall("Incorrect password!".encode('utf-8'))
    return None

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
