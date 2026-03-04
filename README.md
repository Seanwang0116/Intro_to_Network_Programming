# Multiplayer Game Connection Series

This repository contains a series of projects exploring different network architectures and advanced socket programming techniques.

---

## Project 1: P2P Discovery & Handshake
### Overview
A peer-to-peer (P2P) system where players act as both client and server. It focuses on UDP discovery and the transition to a TCP game session.

### Features
* **UDP Discovery**: Scans IP ranges (`140.113.235.151-154`) to find waiting players.
* **Handshake Protocol**: Implements `check` -> `waiting` -> `invite` -> `accept` via UDP.
* **P2P Connection**: The initiator establishes a temporary TCP server to host the game logic.

---

## Project 2: Centralized Lobby & Room System
### Overview
Transitioned from P2P to a **Centralized Server** architecture. A dedicated server manages player states, room creation, and invitations.

### Features
* **Multi-threading**: Server handles multiple concurrent client connections.
* **Account System**: Simple login/registration using CSV-based storage (`user_info.csv`).
* **Lobby Management**: Clients can list online players, create public/private rooms, and join existing matches.
* **Game Logic**: Modularized games (Rock-Paper-Scissors and Tic-Tac-Toe).

---

## Project 3: Dynamic Loading & Advanced Management
### Overview
The final evolution of the system, introducing **Dynamic Game Loading** and enhanced lobby management features.

### Key Enhancements
* **Hot-swappable Games**: The server and client use `importlib` to dynamically load game modules (e.g., `game_1.py`) at runtime without restarting the application.
* **Advanced Invitations**: A robust invitation management system allowing users to accept, reject, or ignore requests.
* **Game Development Management**: A specialized interface for managing new game modules and server-side room states.
* **Scalability**: Improved message handling using `queue` and dedicated threads for server-client communication.

---

## Tech Stack
* **Language**: Python 3.x
* **Protocols**: UDP (Discovery/P1), TCP (Game/Lobby/P2-P3)
* **Libraries**: `socket`, `threading`, `importlib`, `csv`, `queue`

---

## How to Run

### Project 1 (P2P)
1. Run `python Player_B.py` on the receiver side.
2. Run `python Player_A.py` on the initiator side to scan and invite.

### Project 2 & 3 (Centralized)
1. **Start the Server**:
   ```bash
   python server.py
   # Enter the desired port number when prompted
