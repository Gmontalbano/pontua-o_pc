import streamlit as st
import sqlite3
from PIL import Image
from utils.hashes import hash_senha

from pgs.cadastros import cadastro_unidade, cadastro_reuniao, cadastro_membro, cadastro_usuarios, gerenciar_usuario
from pgs.chamadas import registrar_chamada, visualizar_chamada, delete
from pgs.relatorios import show_relatorios

if "loggin" not in st.session_state:
    st.session_state.loggin = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = 0


def main():
    conn = sqlite3.connect("registro_chamada.db")
    cursor = conn.cursor()

    img, title_text = st.columns([1, 2])
    image = Image.open('imgs/pc_logo.jpg')
    img.image(image, caption='Mais que um clube, uma familia')
    title_text.title("Pioneiros da colina")

    st.sidebar.title("Login section")

    username = st.sidebar.text_input("User Name")
    password = st.sidebar.text_input("Password", type='password')

    botao = st.sidebar.button("Entrar")

    if botao or st.session_state.loggin:
        st.session_state.loggin = True
        senha_hash = hash_senha(password)  # Hash da senha digitada

        # Buscar usuário no banco
        cursor.execute("SELECT nome, permissao FROM usuarios WHERE login = ? AND senha = ?", (username, senha_hash))
        usuario = cursor.fetchone()

        if usuario:
            nome, permissao = usuario
            st.success(f"Bem-vindo, {nome}! Permissão: {permissao}")
            st.session_state.username = nome
            st.session_state.load_state = True

            type_permission = {
                'admin': ["Cadastro de reunião", "Cadastro de unidade", "Cadastro de membros", "Registrar chamada",
                          "Visualizar chamada", "Relatórios", "Usuário do sistema", "Deletar"],
                'associado': ["Cadastro de reunião", "Registrar chamada", "Visualizar chamada", "Relatórios"],
                'equipe': ["Registrar chamada", "Visualizar chamada", "Relatórios"],
                'conselho': ["Visualizar chamada", "Relatórios"]
                }
            menu = type_permission[permissao]

            choice = st.sidebar.selectbox("Selecione uma opção", menu)

            if choice == "Cadastro de reunião":
                cadastro_reuniao(cursor, conn)
            elif choice == "Cadastro de unidade":
                cadastro_unidade(cursor, conn)
            elif choice == "Cadastro de membros":
                cadastro_membro(cursor, conn)
            elif choice == "Registrar chamada":
                registrar_chamada(cursor, conn)
            elif choice == "Visualizar chamada":
                visualizar_chamada(conn)
            elif choice == "Relatórios":
                show_relatorios(conn)
            elif choice == "Usuário do sistema":
                aba = st.radio("Selecione uma opção:", ["Cadastrar Usuário", "Gerenciar Usuários"])
                if aba == "Cadastrar Usuário":
                    cadastro_usuarios(cursor, conn)
                elif aba == "Gerenciar Usuários":
                    gerenciar_usuario(cursor, conn)
            elif choice == "Deletar":
                delete(cursor, conn)

        else:
            st.sidebar.error("Incorrect Username/Password")


if __name__ == '__main__':
    main()
