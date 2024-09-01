# message_server.py
import Pyro4
import stomp
import time

@Pyro4.expose
class MessageServer:
    def __init__(self):
        self.queues = {}  # Armazena filas de mensagens para cada cliente
        self.clients = set()  # Armazena o estado de cada cliente (online/offline)
        self.client_states = {}  # Armazena o estado de cada cliente (online/offline)
        self.conn = stomp.Connection11()  # Conexão com o broker STOMP
        self.conn.connect('admin', 'admin', wait=True)
        self.conn.subscribe(destination='/queue/clients', id=1, ack='auto')

    def create_queue(self, client_name):
        if client_name not in self.queues:
            self.queues[client_name] = []

    def register_client(self, client_name):
        self.clients.add(client_name)
        self.client_states[client_name] = False  # Inicialmente offline
        self.create_queue(client_name)
        # Notifica todos os clientes sobre o novo cliente
        for client in self.clients:
            if client != client_name:
                self.conn.send(destination=f'/queue/{client}', body=f'{client_name} entrou no sistema.')

    def deregister_client(self, client_name):
        if client_name in self.clients:
            self.clients.remove(client_name)
            del self.client_states[client_name]
            del self.queues[client_name]

    def set_online(self, client_name):
        self.client_states[client_name] = True

    def set_offline(self, client_name):
        self.client_states[client_name] = False

    def send_message(self, from_client, to_client, message):
        if self.client_states.get(to_client, False):  # Se o cliente está online
            self.conn.send(destination=f'/queue/{to_client}', body=f'{from_client}: {message}')
        else:  # Se o cliente está offline
            self.queues[to_client].append((from_client, message))

    def get_messages(self, client_name):
        if client_name in self.queues:
            messages = self.queues[client_name]
            self.queues[client_name] = []  # Limpa as mensagens após a leitura
            return messages
        return []

    def get_all_clients(self):
        return list(self.clients)

    def subscribe(self, client_name):
        self.conn.subscribe(destination=f'/queue/{client_name}', id=1, ack='auto')

    def unsubscribe(self, client_name):
        self.conn.unsubscribe(destination=f'/queue/{client_name}', id=1)

    def run(self):
        while True:
            time.sleep(1)

def main():
    Pyro4.Daemon.serveSimple(
        {
            MessageServer(): "example.message.server"
        },
        ns=True
    )

if __name__ == "__main__":
    main()
