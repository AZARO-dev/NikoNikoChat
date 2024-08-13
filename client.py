import tkinter as tk
import ctypes
import threading
import socket
import random
from datetime import datetime

class Marquee(tk.Canvas):
    def __init__(self, parent, fps=60, min_speed=2, max_speed=10, text_color="white", font=("Helvetica", 24), **kwargs):
        super().__init__(parent, **kwargs)
        self.fps = fps
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.text_color = text_color
        self.font = font
        self.pack(expand=True, fill='both')

        self.texts = []
        self.update_text_positions()

    def start_text(self, display_text):
        speed = self.get_speed(len(display_text))
        y_position = random.randint(0, self.winfo_height() - 30)
        text_id = self.create_text(self.winfo_width(), y_position, text=display_text, anchor="nw", fill=self.text_color, font=self.font)
        self.texts.append((text_id, speed))

    def get_speed(self, text_length):
        speed = max(self.min_speed, min(self.max_speed, self.max_speed - text_length // 10))
        return speed

    def update_text_positions(self):
        for text_id, speed in list(self.texts):
            self.move(text_id, -speed, 0)
            x0, y0, x1, y1 = self.bbox(text_id)
            if x1 < 0:
                self.delete(text_id)
                self.texts.remove((text_id, speed))
        self.after(int(1000 / self.fps), self.update_text_positions)
    

def make_window_transparent(window):
    window.attributes('-alpha', 0.0)  # 一時的にウィンドウを透明にする
    window.update_idletasks()  # ウィンドウのサイズと位置を更新
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20)
    window.attributes('-alpha', 1.0)  # ウィンドウを再表示

def open_input_window(root, marquee, client_socket, server_address):
    input_window = tk.Toplevel(root)
    input_window.title("Input Text")
    input_window.geometry("400x200")

    tk.Label(input_window, text="Name:").pack(side=tk.TOP, pady=5)
    name_entry = tk.Entry(input_window)
    name_entry.pack(side=tk.TOP, fill=tk.X, padx=10)

    tk.Label(input_window, text="Text:").pack(side=tk.TOP, pady=5)
    text_entry = tk.Entry(input_window)
    text_entry.pack(side=tk.TOP, fill=tk.X, padx=10)

    def send_text():
        name = name_entry.get()
        text = text_entry.get()
        if name and text:
            message = f"{name}: {text}"
            client_socket.sendto(message.encode(), server_address)
            text_entry.delete(0, tk.END)

    text_entry.bind("<Return>", lambda event: send_text())

    tk.Button(input_window, text="Send", command=send_text).pack(side=tk.TOP, pady=10)

def receive_messages(client_socket, marquee, server_address,log_text):
    while True:
        try:
            message, _ = client_socket.recvfrom(1024)
            decoded_message = message.decode()
            update_log_window(log_text, message.decode())

            if decoded_message == "heartbeat":
                # サーバからのハートビートに応答
                client_socket.sendto("heartbeat_ack".encode(), server_address)
            elif decoded_message == "heartbeat_ack":
                # 応答は無視
                continue
            else:
                marquee.start_text(decoded_message)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def quit_me(root_window):
        root_window.quit()
        root_window.destroy()

def create_log_window():
    log_window = tk.Toplevel()
    log_window.title("Log Window")
    log_window.geometry("400x400")

    log_text = tk.Text(log_window, state='disabled', wrap='word')
    log_text.pack(expand=True, fill='both')

    return log_text

def update_log_window(log_text, message):
    if message!="heartbeat":
        log_text.config(state='normal')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_text.insert('1.0', timestamp+" - "+message + '\n')  # 最新メッセージを上部に挿入
        log_text.config(state='disabled')

def main():
    server_ip = input("Enter server IP: ")
    server_port = int(input("Enter server port: "))
    server_address = (server_ip, server_port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(("", 0))  # クライアントソケットを任意の空きポートにバインド

    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda :quit_me(root))
    root.title("Marquee Chat Client")
    root.geometry("1920x1080")
    root.overrideredirect(True)
    root.lift()
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "black")

    marquee = Marquee(root, bg='black', text_color="white", font=('Helvetica', 24))
    marquee.pack(expand=True, fill='both')

    make_window_transparent(root)
    open_input_window(root, marquee, client_socket, server_address)

    log_text = create_log_window()

    # 修正: server_addressをreceive_messagesに渡す
    threading.Thread(target=receive_messages, args=(client_socket, marquee, server_address,log_text)).start()

    def on_resize(event):
        marquee.config(width=event.width, height=event.height)

    root.bind("<Configure>", on_resize)
    
    def on_closing():
        root.destroy()
        client_socket.close()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
