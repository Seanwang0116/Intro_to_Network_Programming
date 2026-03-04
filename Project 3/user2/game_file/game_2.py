import time
from queue import Empty
handle_msg = [
    'Waiting...',
    'This cell has already taken, choose another!',
    'Invalid choice, try again!',
    "You Win!",
    "You Lose!",
    "Draw!",
    '---+---+---',
]

board  = [[" " for _ in range(3)] for _ in range(3)]    

def clear_board():
    return [[" " for _ in range(3)] for _ in range(3)]

def construct_board(board):
    msg_board = ""
    idx = 0
    for i in range(5):
        for j in range(11):
            if j in [1, 5, 9] and i in [0, 2, 4]:
                msg_board += board[i // 2][j // 4]
            elif j in [3, 7]:
                if i in [0, 2, 4]:
                    msg_board += '|'
                elif i in [1, 3]:
                    msg_board += '+'
            elif i in [1, 3]:
                msg_board += '-'
            else:
                msg_board += ' '
        msg_board += '\n'
        if i % 2 == 0:
            idx += 1
    return msg_board

def update_board(board, x, y, marker):
    board[x][y] = marker

def check_board(board, marker):
    for row in board:
        if all(cell == marker for cell in row):
            return True
        
    for col in range(3):
        if all(board[row][col] == marker for row in range(3)):
            return True
        
    if all(board[i][i] == marker for i in range(3)):
        return True
    
    if all(board[i][2 - i] == marker for i in range(3)):
        return True
    
    return False

def main(conn, creator_queue):
    global board
    board = clear_board()
    
    msg_board = construct_board(board)
    print(msg_board, end='')
    count = 0
    while True:
        command = 'Please enter the cell to fill (top-left is (1, 1), separated by a space): '
        conn.sendall('Waiting...'.encode('utf-8'))
        print(command, end='', flush=True)

        while True:
            try:
                server_choice = creator_queue.get(timeout=0.1)
                choice = server_choice.split()
                if len(choice) == 2:
                    y, x = choice
                    if x.isdigit() and y.isdigit() and 1 <= int(x) <= 3 and 1 <= int(y) <= 3:
                        x = int(x) - 1
                        y = int(y) - 1
                        if board[y][x] == " ":
                            break
                        else:
                            print('This cell has already taken, choose another!')
                            print(command, end='', flush=True)
                            
                print('Invalid choice, try again!')
                print(command, end='', flush=True)
            except Empty:
                pass
    
        update_board(board, y, x, 'O')
        if check_board(board, 'O'):
            print("You Win!")
            conn.sendall("You Lose!".encode('utf-8'))
            time.sleep(0.001)
            break
            
        updated_board = construct_board(board)
        conn.sendall(updated_board.encode('utf-8'))
        time.sleep(0.001)
        count += 1

        print('Waiting...')
        while True:
            conn.sendall(command.encode('utf-8'))

            player_choice = conn.recv(1024).decode('utf-8')
            choice = player_choice.split()
            if len(choice) == 2:
                y, x = choice
                if x.isdigit() and y.isdigit() and 1 <= int(x) <= 3 and 1 <= int(y) <= 3:
                    x = int(x) - 1
                    y = int(y) - 1
                    if board[y][x] == " ":
                        break
                    else:
                        conn.sendall('This cell has already taken, choose another!'.encode('utf-8'))
                        time.sleep(0.001)
                        continue
            conn.sendall('Invalid choice, try again!'.encode('utf-8'))
            time.sleep(0.001)
    
        update_board(board, y, x, 'X')
        
        if check_board(board, 'X'):
            print("You Lose!")
            conn.sendall("You Win!".encode('utf-8'))
            time.sleep(0.01)
            break
        if count == 9:
            msg = "Draw!"
            print(msg)
            conn.sendall(msg.encode('utf-8'))
            time.sleep(0.001)
            break
        
        updated_board = construct_board(board)
        print(updated_board)
        count += 1
