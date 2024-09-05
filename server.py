import Pyro4
import stomp

@Pyro4.expose
class MessageServer:
    def __init__(self):
        self.queues = {}  # Armazena filas de mensagens para cada cliente
        self.clients = set()  # Armazena o estado de cada cliente (online/offline)
        self.client_states = {}
        self.client_contacts = {}
        self.subscription_ids = {}  # Armazena os IDs de inscrição para cada cliente
        self.conn = stomp.Connection11()  # Conexão com o broker STOMP
        self.conn.connect('admin', 'admin', wait=True)

    def create_queue(self, client_name):
        if client_name not in self.queues:
            self.queues[client_name] = []
            # Gerar um ID único para a inscrição
            subscription_id = len(self.queues)
            self.subscription_ids[client_name] = subscription_id
            self.conn.subscribe(destination=f'/queue/{client_name}', id=subscription_id, ack='auto')

    def register_client(self, client_name):
        self.clients.add(client_name)
        self.client_states[client_name] = False  # Inicialmente offline
        self.create_queue(client_name)
        self.client_contacts[client_name] = set()  # Inicialmente sem contatos

    def deregister_client(self, client_name):
        if client_name in self.clients:
            self.clients.remove(client_name)
            del self.client_states[client_name]
            del self.queues[client_name]
            del self.client_contacts[client_name]
            # Remover a inscrição associada ao cliente
            if client_name in self.subscription_ids:
                del self.subscription_ids[client_name]

    def set_online(self, client_name):
        self.client_states[client_name] = True
        # Reinscrever para receber mensagens
        subscription_id = self.subscription_ids.get(client_name)
        if subscription_id is not None:
            self.conn.subscribe(destination=f'/queue/{client_name}', id=subscription_id, ack='auto')

        # Enviar mensagens pendentes para o cliente que ficou online
        pending_messages = self.get_messages(client_name)
        for from_client, message in pending_messages:
            self.conn.send(destination=f'/queue/{client_name}', body=f'{from_client}: {message}')

    def set_offline(self, client_name):
        self.client_states[client_name] = False
        self.unsubscribe_from_client_queues(client_name)  # Cancelar inscrição da fila

    def send_message(self, from_client, to_client, message):
        if self.client_states.get(to_client, False):
            self.conn.send(destination=f'/queue/{to_client}', body=f'{from_client}: {message}')
        else:
            if to_client in self.queues:
                self.queues[to_client].append((from_client, message))  # Armazena a mensagem para entrega posterior

    def get_messages(self, client_name):
        if client_name in self.queues:
            messages = self.queues[client_name]
            self.queues[client_name] = []  # Limpa as mensagens após leitura
            return messages
        return []

    def add_contact(self, client_name, contact_name):
        if client_name in self.client_contacts:
            self.client_contacts[client_name].add(contact_name)

    def remove_contact(self, client_name, contact_name):
        if client_name in self.client_contacts:
            self.client_contacts[client_name].discard(contact_name)

    def unsubscribe_from_client_queues(self, client_name):
        if client_name in self.subscription_ids:
            # Usar o ID de inscrição ao cancelar a inscrição
            subscription_id = self.subscription_ids[client_name]
            self.conn.unsubscribe(id=subscription_id)

    def get_all_clients(self):
        return list(self.clients)

def main():
    Pyro4.Daemon.serveSimple(
        {
            MessageServer(): "example.message.server"
        },
        ns=True)

if __name__ == "__main__":
    main()
