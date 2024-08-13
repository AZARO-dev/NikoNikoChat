import socket
import threading
import time

class ChatServer:
    def __init__(self, host='127.0.0.1', port=5000, heartbeat_interval=1):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        self.clients = {}
        self.heartbeat_interval = heartbeat_interval
        print(f"Server started on {host}:{port}")

    def broadcast(self, message):
        disconnected_clients = set()
        for client in self.clients:
            try:
                self.server.sendto(message, client)
            except Exception as e:
                print(f"Failed to send message to {client}: {e}")
                disconnected_clients.add(client)

        for client in disconnected_clients:
            self.clients.pop(client, None)

    def handle_client(self):
        while True:
            try:
                message, address = self.server.recvfrom(1024)
                decoded_message = message.decode()

                if address not in self.clients:
                    self.clients[address] = time.time()
                    print(f"New client connected: {address}")
                else:
                    self.clients[address] = time.time()

                if decoded_message == "heartbeat":
                    # ハートビートに対して応答を送信
                    self.server.sendto("heartbeat_ack".encode(), address)
                elif decoded_message == "heartbeat_ack":
                    # クライアントからの応答があった場合は時間を更新
                    self.clients[address] = time.time()
                else:
                    print(f"Received message from {address}: {decoded_message}")
                    self.broadcast(message)
            except Exception as e:
                print(f"Error handling client: {e}")
                continue

    def check_heartbeat(self):
        while True:
            time.sleep(self.heartbeat_interval)
            current_time = time.time()
            disconnected_clients = []

            for client in list(self.clients):
                try:
                    self.server.sendto("heartbeat".encode(), client)
                except Exception as e:
                    print(f"Failed to send heartbeat to {client}: {e}")
                    disconnected_clients.append(client)
                    continue

                if current_time - self.clients[client] > self.heartbeat_interval * 1.5:
                    print(f"Client {client} did not respond to heartbeat.")
                    disconnected_clients.append(client)

            for client in disconnected_clients:
                print(f"Removing client {client} due to no response.")
                self.clients.pop(client, None)

    def start(self):
        threading.Thread(target=self.handle_client).start()
        threading.Thread(target=self.check_heartbeat).start()

if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server shutting down.")
