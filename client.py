import stomp
import tkinter as tk
from tkinter import simpledialog, scrolledtext


class ChatListener(stomp.ConnectionListener):
    def __init__(self, client):
        self.client = client

    def on_message(self, frame):
        headers = frame.headers
        message = frame.body
        print(f"Message received: {message}")

        # Atualiza a janela de mensagens na thread principal do Tkinter
        self.client.root.after(0, self.client.append_received_message, f"Received: {message}")

    def on_error(self, headers, message):
        print(f"Error received: {message}")

    def on_disconnected(self):
        print("Disconnected from broker")


class ChatClient:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.conn = None
        self.is_connected = False
        self.selected_contact = None  # Contato selecionado para iniciar a conversa

        # Interface do usuário
        self.setup_ui()

    def setup_ui(self):
        self.root.title(f"Chat Application - {self.username}")

        # Frame de contatos
        contacts_frame = tk.Frame(self.root)
        contacts_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.contacts_list = tk.Listbox(contacts_frame)
        self.contacts_list.pack(fill=tk.BOTH, expand=True)

        add_contact_button = tk.Button(contacts_frame, text="Adicionar Contato", command=self.add_contact)
        add_contact_button.pack()

        remove_contact_button = tk.Button(contacts_frame, text="Remover Contato", command=self.remove_contact)
        remove_contact_button.pack()

        start_chat_button = tk.Button(contacts_frame, text="Iniciar Conversa", command=self.start_chat)
        start_chat_button.pack()

        # Botão de conectar/desconectar
        self.connect_button = tk.Button(contacts_frame, text="Conectar", command=self.toggle_connection)
        self.connect_button.pack()

        # Frame de mensagens recebidas
        self.received_frame = tk.Frame(self.root)
        self.received_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(self.received_frame, text="Mensagens Recebidas").pack()
        self.received_messages = scrolledtext.ScrolledText(self.received_frame, wrap=tk.WORD)
        self.received_messages.pack(fill=tk.BOTH, expand=True)

        # Frame de envio de mensagens
        self.send_frame = tk.Frame(self.root)
        self.send_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(self.send_frame)
        self.message_entry.pack(fill=tk.X)

        self.send_button = tk.Button(self.send_frame, text="Send", command=self.send_message)
        self.send_button.pack()

        self.disable_send_panel()  # Inicialmente desativa o painel de envio de mensagens

    def enable_send_panel(self):
        """Habilita o painel de envio de mensagens."""
        self.message_entry.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)

    def disable_send_panel(self):
        """Desabilita o painel de envio de mensagens."""
        self.message_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

    def append_received_message(self, message):
        self.received_messages.insert(tk.END, f"{message}\n")
        self.received_messages.yview(tk.END)  # Auto-scroll para o final

    def add_contact(self):
        contact_name = simpledialog.askstring("Aicionar contato", "Escreva o nome do contato:")
        if contact_name:
            self.contacts_list.insert(tk.END, contact_name)

    def remove_contact(self):
        selected = self.contacts_list.curselection()
        if selected:
            self.contacts_list.delete(selected[0])

    def start_chat(self):
        selected = self.contacts_list.curselection()
        if selected:
            self.selected_contact = self.contacts_list.get(selected[0])
            self.enable_send_panel()
            print(f"Chat iniciado com {self.selected_contact}")

    def send_message(self):
        if self.selected_contact:
            message = self.message_entry.get()
            if message:
                destination = f'/queue/{self.selected_contact}'
                self.conn.send(destination, message)
                print(f"Message sent to {self.selected_contact}: {message}")
                self.message_entry.delete(0, tk.END)

    def connect(self):
        if not self.is_connected:
            self.conn = stomp.Connection([('localhost', 61613)])
            self.conn.set_listener('', ChatListener(self))
            self.conn.connect(wait=True)
            self.conn.subscribe(f'/queue/{self.username}', id=1, ack='auto')
            self.is_connected = True
            print("Connected to broker")
            self.connect_button.config(text="Desconectar")
            self.enable_send_panel()  # Habilita o painel de envio de mensagens ao conectar

    def disconnect(self):
        if self.is_connected:
            self.conn.disconnect()
            self.is_connected = False
            print("Disconnected from broker")
            self.connect_button.config(text="Conectar")
            self.disable_send_panel()  # Desativa o painel de envio de mensagens ao desconectar

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()


def start_chat_app(username):
    root = tk.Tk()
    app = ChatClient(root, username)
    root.mainloop()


if __name__ == "__main__":
    username = simpledialog.askstring("Usuario", "Escreva seu usuario:")
    if username:
        start_chat_app(username)
