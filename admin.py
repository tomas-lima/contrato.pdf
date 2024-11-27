import streamlit as st
import json
import re

# Função para carregar usuários
def load_users():
    with open("users.json", "r") as file:
        return json.load(file)

# Função para salvar usuários
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

# Página de administração
def admin_page():
    st.title("Administração de Usuários")

    # Adicionar usuário
    st.subheader("Adicionar Usuário")
    new_user = st.text_input("Novo Usuário")
    new_password = st.text_input("Senha", type="password")
    confirm_password = st.text_input("Confirme a Senha", type="password")
    role = st.selectbox("Função", ["user", "admin"])

    # Campos adicionais
    unidade = st.text_input("Unidade")
    endereco = st.text_input("Endereço")
    cirurgiao_responsavel = st.text_input("Cirurgião Dentista Responsável")

    if st.button("Adicionar"):
        users = load_users()

        # Verificar se o nome do usuário é válido
        if not new_user.strip():
            st.error("O nome do usuário não pode estar vazio.")
        elif " " in new_user:
            st.error("O nome do usuário não pode conter espaços.")
        elif not re.match("^[a-zA-Z0-9_-]+$", new_user):
            st.error("O nome do usuário pode conter apenas letras, números, hífens e underscores.")
        elif new_user in users:
            st.error("Usuário já existe!")
        elif not new_password.strip():
            st.error("A senha não pode estar vazia.")
        elif new_password != confirm_password:
            st.error("As senhas não coincidem. Por favor, tente novamente.")
        elif not unidade.strip():
            st.error("A unidade não pode estar vazia.")
        elif not endereco.strip():
            st.error("O endereço não pode estar vazio.")
        elif not cirurgiao_responsavel.strip():
            st.error("O cirurgião dentista responsável não pode estar vazio.")
        else:
            # Adicionar o novo usuário com dados adicionais
            users[new_user] = {
                "password": new_password,
                "role": role,
                "unidade": unidade,
                "endereco": endereco,
                "cirurgiao_responsavel": cirurgiao_responsavel,
            }
            save_users(users)
            st.success(f"Usuário {new_user} adicionado com sucesso!")

    # Remover usuário
    st.subheader("Remover Usuário")
    user_to_remove = st.selectbox("Selecione o usuário", list(load_users().keys()))

    if st.button("Remover"):
        users = load_users()
        if user_to_remove in users:
            del users[user_to_remove]
            save_users(users)
            st.success(f"Usuário {user_to_remove} removido com sucesso!")

# Função principal
def main():
    if st.session_state.get("role") != "admin":
        st.error("Acesso negado!")
        return
    admin_page()

main()
