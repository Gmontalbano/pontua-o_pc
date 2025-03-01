import streamlit as st
import sqlite3
from PIL import Image
from utils.hashes import hash_senha

from pgs.cadastros import cadastro_unidade, cadastro_reuniao, delete_reuniao, cadastro_membro, delete_membro, gerenciar_usuarios
from pgs.chamadas import registrar_chamada, visualizar_chamada
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
        cursor.execute("""
            SELECT membros.Nome, usuarios.permissao 
            FROM usuarios 
            JOIN membros ON usuarios.codigo_sgc = membros.codigo_sgc 
            WHERE usuarios.login = ? AND usuarios.senha = ?
        """, (username, senha_hash))

        usuario = cursor.fetchone()

        if usuario:
            nome, permissao = usuario
            st.success(f"Bem-vindo, {nome}! Permissão: {permissao}")
            st.session_state.username = nome
            st.session_state.load_state = True

            type_permission = {
                'admin': ["Reuniões", "Membros", "Chamada", "Cadastro de unidade",
                          "Visualizar chamada", "Relatórios", "Usuário do sistema"],
                'associado': ["Reuniões","Membros", "Chamada", "Visualizar chamada", "Relatórios", "Usuário do sistema"],
                'equipe': ["Chamada", "Visualizar chamada", "Relatórios"],
                'conselho': ["Relatórios"]
                }
            menu = type_permission[permissao]

            # Cria as abas com as opções disponíveis para o usuário
            tabs = st.tabs(menu)

            # Lógica para exibir a função correspondente à aba ativa
            for i, tab in enumerate(tabs):
                with tab:
                    if menu[i] == "Reuniões":
                        with st.expander("cadastrar"):
                            cadastro_reuniao(cursor, conn)
                        with st.expander("Editar"):
                            delete_reuniao(cursor, conn)
                    elif menu[i] == "Cadastro de unidade":
                        cadastro_unidade(cursor, conn)
                    elif menu[i] == "Membros":
                        with st.expander("cadastrar"):
                            cadastro_membro(cursor, conn)
                        with st.expander("Editar"):
                            delete_membro(cursor, conn)
                    elif menu[i] == "Chamada":
                        registrar_chamada(cursor, conn)
                    elif menu[i] == "Visualizar chamada":
                        visualizar_chamada(conn)
                    elif menu[i] == "Relatórios":
                        show_relatorios(conn)
                    elif menu[i] == "Usuário do sistema":
                        gerenciar_usuarios(cursor, conn)

        else:
            st.sidebar.error("Incorrect Username/Password")


if __name__ == '__main__':
    main()