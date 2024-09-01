# client.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import Pyro4
import stomp


class ChatClient:
    def __init__(self):
        self.name = None
        self.server = None
        self.conn = None
        self.create_login_ui()

    def create_login_ui(self):
        self.login_root = tk.Tk()
        self.login_root.title("Login")

        tk.Label(self.login_root, text="Nome de Contato:").pack(pady=5)
        self.name_entry = tk.Entry(self.login_root)
        self.name_entry.pack(pady=5)
        tk.Button(self.login_root, text="Entrar", command=self.login).pack(pady=5)

        self.login_root.mainloop()

    def login(self):
        self.name = self.name_entry.get().strip()
        if self.name:
            try:
                self.server = Pyro4.Proxy("PYRONAME:example.message.server")
                self.conn = stomp.Connection11()
                self.conn.connect('admin', 'admin', wait=True)
                self.conn.subscribe(destination=f'/queue/{self.name}', id=1, ack='auto')

                # Criar fila para o cliente
                self.server.create_queue(self.name)

                self.login_root.destroy()
                self.create_ui()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao conectar ao servidor: {e}")

    def create_ui(self):
        self.root = tk.Tk()
        self.root.title(f"Chat - {self.name}")

        # Frame para a lista de contatos
        self.contacts_frame = tk.Frame(self.root)
        self.contacts_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(self.contacts_frame, text="Contatos").pack()

        self.contacts_listbox = tk.Listbox(self.contacts_frame, selectmode=tk.SINGLE)
        self.contacts_listbox.pack(fill=tk.BOTH, expand=True)

        # Botões para adicionar e remover contatos
        tk.Button(self.contacts_frame, text="Adicionar Contato", command=self.add_contact).pack(pady=5)
        tk.Button(self.contacts_frame, text="Remover Contato", command=self.remove_contact).pack(pady=5)

        # Frame para o chat
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_area = tk.Text(self.chat_frame, state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(self.chat_frame)
        self.entry.pack(fill=tk.X, pady=5)
        self.entry.bind("<Return>", self.send_message)

        # Atualizar mensagens periodicamente
        self.root.after(1000, self.update_messages)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def add_contact(self):
        contact_name = simpledialog.askstring("Adicionar Contato", "Nome do contato:")
        if contact_name:
            if contact_name not in self.contacts_listbox.get(0, tk.END):
                self.contacts_listbox.insert(tk.END, contact_name)
                self.server.subscribe(contact_name)
            else:
                messagebox.showinfo("Info", "Contato já está na lista.")

    def remove_contact(self):
        selected_contact = self.contacts_listbox.get(tk.ACTIVE)
        if selected_contact:
            self.contacts_listbox.delete(tk.ACTIVE)
            self.server.unsubscribe(selected_contact)
        else:
            messagebox.showwarning("Aviso", "Nenhum contato selecionado.")

    def send_message(self, event=None):
        recipient = self.contacts_listbox.get(tk.ACTIVE)
        if recipient:
            message = self.entry.get()
            if message:
                self.server.send_message(self.name, recipient, message)
                self.entry.delete(0, tk.END)

    def update_messages(self):
        messages = self.server.get_messages(self.name)
        for from_client, message in messages:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.insert(tk.END, f'{from_client}: {message}\n')
            self.text_area.config(state=tk.DISABLED)
        self.root.after(1000, self.update_messages)

    def on_closing(self):
        self.server.unsubscribe(self.name)
        self.root.destroy()


def main():
    ChatClient()


if __name__ == "__main__":
    main()
