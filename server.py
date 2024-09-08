import tkinter as tk
from tkinter import messagebox
import Pyro4
import stomp
import threading
import json
from collections import defaultdict

class ServerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Servidor de Mensagens")

        # Interface
        self.ip_label = tk.Label(root, text="IP do Servidor de Nomes:")
        self.ip_label.pack(pady=5)

        self.ip_entry = tk.Entry(root)
        self.ip_entry.pack(pady=5)

        self.start_button = tk.Button(root, text="Iniciar Servidor", command=self.start_server)
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(root, text="Status: Offline", fg="red")
        self.status_label.pack(pady=10)

        # Inicializa o servidor
        self.server = None
        self.server_thread = None

    def start_server(self):
        nameserver_ip = self.ip_entry.get()
        if not nameserver_ip:
            messagebox.showerror("Erro", "O IP do servidor de nomes não pode estar vazio.")
            return

        # Inicia o servidor em uma nova thread para não bloquear a interface gráfica
        if self.server_thread is None or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(target=self.run_server, args=(nameserver_ip,))
            self.server_thread.start()
            self.status_label.config(text="Status: Online", fg="green")

    def run_server(self, nameserver_ip):
        """ Função para iniciar o servidor Pyro4 """
        daemon = Pyro4.Daemon(nameserver_ip)
        server = MessageServer()
        ns = Pyro4.locateNS()
        uri = daemon.register(server)
        ns.register("TESTE", uri)

        print("Servidor Pyro4 iniciado. Aguardando requisições...")
        server.connect_to_broker()
        daemon.requestLoop()

    def stop_server(self):
        """ Encerra o servidor e atualiza o status """
        if self.server:
            self.server.stop()
            self.status_label.config(text="Status: Offline", fg="red")
@Pyro4.expose
class MessageServer:
    def __init__(self):
        self.clients = []
        self.stomp_connection = None
        self.message_queues = defaultdict(list)
        self.client_online_status = defaultdict(bool)

    def connect_to_broker(self, host='localhost', port=61613):
        """ Conecta ao broker STOMP e configura o listener de mensagens """
        self.stomp_connection = stomp.Connection([(host, port)])
        self.stomp_connection.set_listener('', BrokerListener(self))
        self.stomp_connection.connect(wait=True)
        print("Connected to broker STOMP")

    def register_client(self, client_name):
        """ Registra um cliente e cria uma fila para ele no broker """
        self.clients.append({"nome": client_name, "notify": False, "message": ""})
        self.stomp_connection.subscribe(f'/queue/{client_name}', id=1, ack='auto')
        self.client_online_status[client_name] = True
        print(f"Client {client_name} registered and subscribed to queue")

    def get_clients(self):
        """ Retorna a lista de clientes com suas mensagens e notificações """
        return self.clients

    def msg_acknowledge(self, client_name):
        """ Reconhece a mensagem recebida e reseta a notificação """
        for client in self.clients:
            if client["nome"] == client_name:
                client["notify"] = False
                client["message"] = ""
                break

    def msg_callback(self, body):
        """ Callback para quando uma mensagem é recebida do broker """
        content = json.loads(body)
        sender = content['sender']
        receiver = content['receiver']
        message = content['message']
        print(f'Message received from {sender} to {receiver}: {message}')

        if not self.client_online_status[receiver]:
            self.message_queues[receiver].append(f'{sender}: {message}')
        else:
            for client in self.clients:
                if client["nome"] == receiver:
                    client["notify"] = True
                    client["message"] = f'{sender}: {message}'
                    break

    def send_message(self, sender, receiver, message):
        """ Envia uma mensagem de um cliente para outro através do broker """
        content = json.dumps({"sender": sender, "receiver": receiver, "message": message})
        self.stomp_connection.send(destination=f'/queue/{receiver}', body=content)
        print(f"Message sent from {sender} to {receiver}: {message}")

    def set_client_status(self, client_name, is_online):
        """ Atualiza o status de um cliente (conectado/desconectado) """
        self.client_online_status[client_name] = is_online

    def get_pending_messages(self, client_name):
        """ Retorna todas as mensagens pendentes para o cliente """
        messages = self.message_queues[client_name]
        self.message_queues[client_name] = []
        return messages

class BrokerListener(stomp.ConnectionListener):
    def __init__(self, server):
        self.server = server

    def on_message(self, frame):
        message_body = frame.body
        self.server.msg_callback(message_body)

    def on_error(self, headers, message):
        print(f"Error received: {message}")

    def on_disconnected(self):
        print("Disconnected from broker")

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
