# client.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import Pyro4


class ChatClient:
    def __init__(self):
        self.name = None
        self.server = None
        self.current_conversation = None
        self.create_login_ui()

    def create_login_ui(self):
        self.login_root = tk.Tk()
        self.login_root.title("Login")

        tk.Label(self.login_root, text="Digite seu usuário:").pack(pady=5)
        self.name_entry = tk.Entry(self.login_root)
        self.name_entry.pack(pady=5)
        tk.Button(self.login_root, text="Entrar", command=self.login).pack(pady=5)

        self.login_root.mainloop()

    def login(self):
        self.name = self.name_entry.get().strip()
        if self.name:
            try:
                self.server = Pyro4.Proxy("PYRONAME:example.message.server")
                self.server.register_client(self.name)

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

        # Botão para adicionar contatos
        tk.Button(self.contacts_frame, text="Adicionar Contato", command=self.add_contact).pack(pady=5)

        # Botão para iniciar conversa
        tk.Button(self.contacts_frame, text="Iniciar Conversa", command=self.start_conversation).pack(pady=5)

        # Frame para a conversa
        self.conversation_frame = tk.Frame(self.root)
        self.conversation_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def add_contact(self):
        contact_name = simpledialog.askstring("Adicionar Contato", "Digite o nome do contato:")
        if contact_name:
            contact_name = contact_name.strip()
            if contact_name and contact_name != self.name:
                try:
                    # Adiciona o contato à lista de contatos local
                    self.contacts_listbox.insert(tk.END, contact_name)
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao adicionar contato: {e}")
            else:
                messagebox.showwarning("Aviso", "Nome de contato inválido.")

    def start_conversation(self):
        selected_contact = self.contacts_listbox.get(tk.ACTIVE)
        if selected_contact:
            if self.current_conversation:
                self.current_conversation.destroy()
            self.current_conversation = ConversationFrame(self.conversation_frame, self.server, self.name, selected_contact)
        else:
            messagebox.showwarning("Aviso", "Nenhum contato selecionado.")

    def on_closing(self):
        self.server.deregister_client(self.name)
        self.server.set_offline(self.name)
        self.root.destroy()


class ConversationFrame(tk.Frame):
    def __init__(self, master, server, my_name, contact_name):
        super().__init__(master)
        self.server = server
        self.my_name = my_name
        self.contact_name = contact_name

        self.pack(fill=tk.BOTH, expand=True)

        self.text_area = tk.Text(self, state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(self)
        self.entry.pack(fill=tk.X, pady=5)
        self.entry.bind("<Return>", self.send_message)

        # Adiciona título informando com quem está conversando
        self.title_label = tk.Label(self, text=f"Conversa com {contact_name}", font=("Arial", 12, "bold"))
        self.title_label.pack(pady=5)

        # Atualiza mensagens periodicamente
        self.update_messages()

    def send_message(self, event=None):
        message = self.entry.get()
        if message:
            self.server.send_message(self.my_name, self.contact_name, message)
            self.display_message(self.my_name, message, is_sent=True)
            self.entry.delete(0, tk.END)

    def update_messages(self):
        messages = self.server.get_messages(self.my_name)
        for from_client, message in messages:
            if from_client == self.contact_name:
                self.display_message(from_client, message, is_sent=False)
        self.after(1000, self.update_messages)

    def display_message(self, from_client, message, is_sent):
        self.text_area.config(state=tk.NORMAL)
        if is_sent:
            self.text_area.insert(tk.END, f'Você: {message}\n', 'sent')
        else:
            self.text_area.insert(tk.END, f'{from_client}: {message}\n', 'received')
        self.text_area.config(state=tk.DISABLED)
        self.text_area.yview(tk.END)  # Auto-scroll para o final


def main():
    ChatClient()


if __name__ == "__main__":
    main()
