import tkinter as tk
from client import Cliente

class InterfaceCliente:
    def __init__(self, cliente):
        self.cliente = cliente
        self.root = tk.Tk()
        self.root.title(f"Cliente {self.cliente.nome}")

        self.lbl_mensagem = tk.Label(self.root, text="Mensagem:")
        self.lbl_mensagem.pack()

        self.entry_mensagem = tk.Entry(self.root)
        self.entry_mensagem.pack()

        self.lbl_destinatario = tk.Label(self.root, text="Destinatário:")
        self.lbl_destinatario.pack()

        self.entry_destinatario = tk.Entry(self.root)
        self.entry_destinatario.pack()

        self.btn_enviar = tk.Button(self.root, text="Enviar", command=self.enviar_mensagem)
        self.btn_enviar.pack()

        self.btn_online = tk.Button(self.root, text="Online", command=lambda: self.cliente.mudar_estado("online"))
        self.btn_online.pack()

        self.btn_offline = tk.Button(self.root, text="Offline", command=lambda: self.cliente.mudar_estado("offline"))
        self.btn_offline.pack()

        self.btn_receber = tk.Button(self.root, text="Receber Mensagens Offline", command=self.receber_mensagens)
        self.btn_receber.pack()

    def enviar_mensagem(self):
        destinatario = self.entry_destinatario.get()
        mensagem = self.entry_mensagem.get()
        self.cliente.enviar_mensagem(destinatario, mensagem)

    def receber_mensagens(self):
        self.cliente.receber_mensagens_offline()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    nome_cliente = input("Digite o nome do cliente: ")
    cliente = Cliente(nome_cliente)
    interface = InterfaceCliente(cliente)
    interface.run()
