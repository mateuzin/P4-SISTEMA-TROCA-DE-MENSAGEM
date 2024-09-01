# message_server.py
import Pyro4
import stomp
import time

@Pyro4.expose
class MessageServer:
    def __init__(self):
        self.queues = {}  # Armazena filas de mensagens para cada cliente
        self.conn = stomp.Connection11()  # Conexão com o broker STOMP
        self.conn.connect('admin', 'admin', wait=True)
        self.conn.subscribe(destination='/queue/clients', id=1, ack='auto')

    def create_queue(self, client_name):
        if client_name not in self.queues:
            self.queues[client_name] = []

    def send_message(self, from_client, to_client, message):
        if to_client in self.queues:
            self.queues[to_client].append((from_client, message))
        else:
            self.conn.send(destination=f'/queue/{to_client}', body=f'{from_client}: {message}')

    def get_messages(self, client_name):
        if client_name in self.queues:
            messages = self.queues[client_name]
            self.queues[client_name] = []  # Limpa as mensagens após a leitura
            return messages
        return []

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
