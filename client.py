import tkinter as tk
from tkinter import simpledialog, scrolledtext
import Pyro4
import threading


class ChatClient:
    def __init__(self, root, username, nameserver_ip):
        self.root = root
        self.username = username
        self.is_connected = False
        self.selected_contact = None  # Contato selecionado para iniciar a conversa
        self.message_fetch_thread = None

        # Conecta ao servidor Pyro4
        self.message_server = Pyro4.Proxy(f"PYRONAME:TESTE@{nameserver_ip}")

        # Registra o cliente no servidor Pyro4
        self.message_server.register_client(self.username)

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

        self.contact_label = tk.Label(self.send_frame, text="Contato:")
        self.contact_label.pack()

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
        contact_name = simpledialog.askstring("Adicionar contato", "Escreva o nome do contato:")
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
            self.contact_label.config(text=f"Enviando para: {self.selected_contact}")
            self.enable_send_panel()
            print(f"Chat iniciado com {self.selected_contact}")

    def send_message(self):
        if self.selected_contact:
            message = self.message_entry.get()
            if message:
                # Envia a mensagem ao servidor, que a repassa ao broker
                self.message_server.send_message(self.username, self.selected_contact, message)
                print(f"Message sent to {self.selected_contact}: {message}")
                self.message_entry.delete(0, tk.END)

    def toggle_connection(self):
        """Gerencia o estado de conexão/desconexão do cliente."""
        if self.is_connected:
            # Desconecta o cliente
            self.message_server.set_client_status(self.username, False)
            self.is_connected = False
            self.connect_button.config(text="Conectar")
            self.disable_send_panel()
            if self.message_fetch_thread:
                self.message_fetch_thread.join(timeout=1)  # Espera a thread parar
        else:
            # Conecta o cliente
            self.message_server.set_client_status(self.username, True)
            self.is_connected = True
            self.connect_button.config(text="Desconectar")
            self.enable_send_panel()
            self.fetch_pending_messages()  # Busca as mensagens pendentes

    def fetch_pending_messages(self):
        """Busca e exibe mensagens pendentes quando o cliente se conecta."""
        pending_messages = self.message_server.get_pending_messages(self.username)
        for message in pending_messages:
            self.append_received_message(message)

        # Inicia uma nova thread para buscar mensagens periodicamente
        self.message_fetch_thread = threading.Thread(target=self.fetch_messages)
        self.message_fetch_thread.daemon = True
        self.message_fetch_thread.start()

    def fetch_messages(self):
        """Busca periodicamente mensagens do servidor."""
        while self.is_connected:
            clients = self.message_server.get_clients()
            for client in clients:
                if client["nome"] == self.username and client["notify"]:
                    self.append_received_message(client["message"])
                    self.message_server.msg_acknowledge(self.username)
            threading.Event().wait(2)


def start_chat_app(username, nameserver_ip):
    root = tk.Tk()
    app = ChatClient(root, username, nameserver_ip)
    root.mainloop()


if __name__ == "__main__":
    username = simpledialog.askstring("Usuário", "Escreva seu usuário:")
    nameserver_ip = simpledialog.askstring("IP do Servidor de Nomes", "Escreva o IP do Servidor de Nomes Pyro4:")
    if username and nameserver_ip:
        start_chat_app(username, nameserver_ip)
