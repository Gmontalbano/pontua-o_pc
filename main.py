import streamlit as st
import sqlite3
from PIL import Image
from utils.hashes import hash_senha

from pgs.cadastros import cadastro_unidade, cadastro_reuniao, delete_reuniao, cadastro_membro, delete_membro, gerenciar_usuarios
from pgs.chamadas import registrar_chamada, visualizar_chamada
from pgs.relatorios import show_relatorios
from pgs.especialidades import mostrar_especialidades_usuario, gerenciar_especialidades_usuario
from pgs.classes import mostrar_classes_usuario, gerenciar_classes_usuario
from pgs.tesouraria import (criar_mensalidades, visualizar_relatorios, visualizar_debitos, editar_status_mensalidade,
                            criar_eventos, editar_status_inscricao, remover_inscricao, inscrever_no_evento, editar_mensalidade, editar_evento,
                            fechamento_mensal, gerenciar_caixa)

if "loggin" not in st.session_state:
    st.session_state.loggin = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = 0
if "sgc" not in st.session_state:
    st.session_state.sgc = 0

st.set_page_config(layout="wide")


def main():
    conn = sqlite3.connect("registro_chamada.db")
    cursor = conn.cursor()

    img, title_text = st.columns([1, 8])
    image = Image.open('imgs/pc_logo.jpg')
    img.image(image, caption='Mais que um clube, uma familia')
    title_text.title("Pioneiros da colina")

    st.sidebar.title("Login section")

    username = st.sidebar.text_input("User Name")
    password = st.sidebar.text_input("Password", type='password')

    botao = st.sidebar.button("Entrar")

    if botao or st.session_state.loggin:

        senha_hash = hash_senha(password)  # Hash da senha digitada

        # Buscar usuário no banco
        cursor.execute("""
            SELECT membros.Nome, usuarios.permissao, usuarios.codigo_sgc
            FROM usuarios 
            JOIN membros ON usuarios.codigo_sgc = membros.codigo_sgc 
            WHERE usuarios.login = ? AND usuarios.senha = ?
        """, (username, senha_hash))

        usuario = cursor.fetchone()

        if usuario:
            nome, permissao, sgc = usuario
            st.success(f"Bem-vindo, {nome}! Permissão: {permissao} {sgc}")
            st.session_state.username = nome
            st.session_state.sgc = sgc
            st.session_state.load_state = True
            st.session_state.loggin = True

            type_permission = {
                'admin': ["Reuniões", "Membros", "Chamada", "Cadastro de unidade",
                          "Visualizar chamada", "Relatórios", "Usuário do sistema",
                          "Especialidades", "Classes", "Tesouraria"],
                'associado': ["Reuniões", "Membros", "Chamada", "Visualizar chamada",
                              "Relatórios", "Usuário do sistema",
                              "Especialidades", "Classes", "Tesouraria"],
                'equipe': ["Chamada", "Visualizar chamada", "Relatórios"],
                'conselho': ["Relatórios", "Especialidades", "Classes"]
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
                    elif menu[i] == "Especialidades":
                        if permissao == 'conselho':
                            mostrar_especialidades_usuario(conn, st.session_state.sgc)
                        elif permissao == 'associado':
                            mostrar_especialidades_usuario(conn, st.session_state.sgc)
                            gerenciar_especialidades_usuario(conn)
                    elif menu[i] == "Classes":
                        if permissao == 'conselho':
                            mostrar_classes_usuario(conn, st.session_state.sgc)
                        elif permissao == 'associado' or permissao == 'admin':
                            mostrar_classes_usuario(conn, st.session_state.sgc)
                            gerenciar_classes_usuario(conn)
                    elif menu[i] == "Tesouraria":
                        with st.expander("Novo evento"):
                            aba1 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'],
                                                key="cadastrar_opcao")
                            if aba1 == 'Evento':
                                criar_eventos(conn)
                            elif aba1 == 'Mensalidade':
                                criar_mensalidades(conn)

                        with st.expander("Pagamentos"):
                            aba2 = st.selectbox("Escolha uma opção:", ['Mensalidade', 'Evento', 'Débitos',],
                                                key="gerenciar_opcao")
                            if aba2 == 'Mensalidade':
                                editar_status_mensalidade(conn)
                            elif aba2 == 'Evento':
                                editar_status_inscricao(conn)
                            elif aba2 == 'Débitos':
                                visualizar_debitos(conn)

                        with st.expander('Inscrições'):
                            aba3 = st.selectbox("Esolha uma opção:", ['Increver no evento', 'Remover de um evento'])
                            if aba3 == 'Increver no evento':
                                inscrever_no_evento(conn)
                            elif aba3 == 'Remover de um evento':
                                remover_inscricao(conn)

                        with st.expander('Gerenciar eventos'):
                            aba4 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'])
                            if aba4 == 'Evento':
                                editar_evento(conn)
                            if aba4 == 'Mensalidade':
                                editar_mensalidade(conn)

                        with st.expander("Relatórios"):
                            visualizar_relatorios(conn)

                        with st.expander("Caixa"):
                            gerenciar_caixa(conn)

                        with st.expander("Fechamento"):
                            fechamento_mensal(conn)

    else:
        st.sidebar.error("Incorrect Username/Password")


if __name__ == '__main__':
    main()
