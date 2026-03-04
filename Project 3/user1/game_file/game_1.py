import time
from queue import Empty
handle_msg = [
    'Invalid choice, choose again!',
    'Your opponent choose: ',
    'You choose: ',
    "Draw! Next round!",
    "You Win!",
    "You Lose!",
]

def main(conn, creator_queue):
    while True:
        choices = ["paper", "scissor", "stone"]
        question = "Paper? Scissor? Stone?: "
        print(question, end='', flush=True)
        conn.sendall(question.encode('utf-8'))

        while True:
            try:
                server_choice = creator_queue.get(timeout=0.1).lower()
                if server_choice in choices:
                    break
                else:
                    print("Invalid choice, choose again!")
                    print(question, end='', flush=True)
            except Empty:
                pass

        player_choice = conn.recv(1024).decode('utf-8').lower()
        while player_choice not in choices:
            err_msg = "Invalid choice, choose again!"
            conn.sendall(err_msg.encode('utf-8'))
            time.sleep(0.001)
            conn.sendall('Paper? Scissor? Stone?: '.encode('utf-8'))
            player_choice = conn.recv(1024).decode('utf-8').lower()
        
        server_msg = f'Your opponent choose: {server_choice}'
        conn.sendall(server_msg.encode('utf-8'))
        time.sleep(0.001)
        conn.sendall(f"You choose: {player_choice}".encode('utf-8'))
        time.sleep(0.001)
        print(f"Your opponent choose: {player_choice}")
        print(f"You choose: {server_choice}")
        
        win = True
        if player_choice == server_choice:
            result_message = "Draw! Next round!"
        elif (player_choice == "scissor" and server_choice == "paper") or \
             (player_choice == "stone" and server_choice == "scissor") or \
             (player_choice == "paper" and server_choice == "stone"):
            result_message = "You Win!"
            win = False
        else:
            result_message = "You Lose!"
        
        time.sleep(0.001)
        conn.sendall(result_message.encode('utf-8'))
        time.sleep(0.001)
        if result_message == "Draw! Next round!":
            print('Draw! Next round!')
            continue
        if win:
            print("You Win!")
        else:
            print("You Lose!")
        if (result_message != "Draw! Next round!"):
            time.sleep(0.001)
            break
        time.sleep(0.001)