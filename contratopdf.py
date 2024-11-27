import streamlit as st
import json
from contrato import contrato_page
from admin import admin_page

# Função para carregar usuários
def load_users():
    try:
        with open("users.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("Arquivo de usuários não encontrado.")
        return {}

# Tela de login
def login():
    st.title("Sistema de Login")

    # Inicializa os campos no session_state
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "password" not in st.session_state:
        st.session_state["password"] = ""
    if "login_attempt" not in st.session_state:
        st.session_state["login_attempt"] = False  # Para evitar o duplo clique no login

    # Campos de entrada
    st.session_state["username"] = st.text_input("Usuário", value=st.session_state["username"])
    st.session_state["password"] = st.text_input("Senha", type="password", value=st.session_state["password"])

    # Botão de login com callback
    def login_callback():
        users = load_users()
        if st.session_state["username"] in users and users[st.session_state["username"]]["password"] == st.session_state["password"]:
            st.success("Login realizado com sucesso!")
            st.session_state["logged_in"] = True
            st.session_state["login_attempt"] = True
            st.session_state["username_logged_in"] = st.session_state["username"]  # Salva o usuário logado no session_state
            # Define a página com base no papel do usuário
            if users[st.session_state["username"]]["role"] == "admin":
                st.session_state["page"] = "admin"
            else:
                st.session_state["page"] = "contrato"
        else:
            st.session_state["login_attempt"] = False
            st.error("Usuário ou senha incorretos!")

    if not st.session_state["login_attempt"]:
        st.button("Login", on_click=login_callback)  # Evita duplo clique com controle de estado

# Controle de navegação
def main():
    # Inicializa o estado de login
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    # Controle de navegação baseado no estado
    if not st.session_state["logged_in"]:
        login()
    elif st.session_state["page"] == "contrato":
        contrato_page()
    elif st.session_state["page"] == "admin":
        admin_page()
    else:
        st.error("Página não encontrada.")

# Executa a aplicação
if __name__ == "__main__":
    main()

#cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF && ambienteVirtual\Scripts\activate && streamlit run contratopdf.py