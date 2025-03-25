import streamlit as st
from PIL import Image

from utils.hashes import hash_senha

from pgs.cadastros import cadastro_unidade, cadastro_reuniao, delete_reuniao, cadastro_membro, delete_membro, \
    gerenciar_usuarios
from pgs.chamadas import registrar_chamada, visualizar_chamada
from pgs.pontuacao import show_pontos
from pgs.especialidades import mostrar_especialidades_usuario, gerenciar_especialidades_usuario
from pgs.classes import mostrar_classes_usuario, gerenciar_classes_usuario
from pgs.tesouraria import (criar_mensalidades, visualizar_relatorios, visualizar_debitos, editar_status_mensalidade,
                            criar_eventos, editar_status_inscricao, remover_inscricao, inscrever_no_evento,
                            editar_mensalidade, editar_evento,
                            fechamento_mensal, gerenciar_caixa)
from pgs.patrimonio import gerenciar_patrimonio
from pgs.solicitacoes import sol
from pgs.ata import atas_e_atos
from pgs.documentos import docs
from pgs.extracao import aba_extracao

from pgs.db import conect_db, get_usuario

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
        usuario = get_usuario(username, senha_hash)

        if usuario:
            nome, permissao, sgc = usuario
            st.success(f"Bem-vindo, {nome}! Permissão: {permissao} {sgc}")
            st.session_state.username = nome
            st.session_state.sgc = sgc
            st.session_state.load_state = True
            st.session_state.loggin = True

            type_permission = {
                'admin': ["Reuniões", "Membros", "Chamada", "Cadastro de unidade",
                          "Visualizar chamada", "Pontuação", "Usuário do sistema",
                          "Especialidades", "Classes", "Tesouraria"],
                'especialidade': ["Reuniões", "Membros", "Chamada", "Visualizar chamada",
                                  "Pontuação", "Usuário do sistema",
                                  "Especialidades", "Classes", "Tesouraria",
                                  "Patrimonio", "Materiais", "Atas e Atos", "Documentos", "Relatorios"],
                'associado': ["Reuniões", "Membros", "Chamada", "Visualizar chamada", "Pontuação", "Usuário do sistema"],
                'equipe': ["Chamada", "Visualizar chamada", "Pontuação"],
                'conselho': ["Pontuação", "Especialidades", "Classes"]
            }
            menu = type_permission[permissao]

            tabs = st.tabs(menu)

            # Lógica para exibir a função correspondente à aba ativa
            for i, tab in enumerate(tabs):
                with tab:
                    if menu[i] == "Reuniões":
                        with st.expander("cadastrar"):
                            cadastro_reuniao()
                        with st.expander("Editar"):
                            delete_reuniao()
                    elif menu[i] == "Cadastro de unidade":
                        cadastro_unidade()
                    elif menu[i] == "Membros":
                        with st.expander("cadastrar"):
                            cadastro_membro()
                        with st.expander("Editar"):
                            delete_membro()
                    elif menu[i] == "Chamada":
                        registrar_chamada()
                    elif menu[i] == "Visualizar chamada":
                        visualizar_chamada()
                    elif menu[i] == "Pontuação":
                        show_pontos()
                    elif menu[i] == "Usuário do sistema":
                        gerenciar_usuarios()
                    elif menu[i] == "Especialidades":
                        if permissao == 'conselho':
                            mostrar_especialidades_usuario(st.session_state.sgc)
                        elif permissao == 'associado':
                            mostrar_especialidades_usuario(st.session_state.sgc)
                            gerenciar_especialidades_usuario()
                    elif menu[i] == "Classes":
                        if permissao == 'conselho':
                            mostrar_classes_usuario(st.session_state.sgc)
                        elif permissao == 'associado' or permissao == 'admin':
                            mostrar_classes_usuario(codigo_sgc=st.session_state.sgc)
                            gerenciar_classes_usuario()
                    elif menu[i] == "Tesouraria":
                        with st.expander("Novo evento"):
                            aba1 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'],
                                                key="cadastrar_opcao")
                            if aba1 == 'Evento':
                                criar_eventos()
                            elif aba1 == 'Mensalidade':
                                criar_mensalidades()

                        with st.expander("Pagamentos"):
                            aba2 = st.selectbox("Escolha uma opção:", ['Mensalidade', 'Evento', 'Débitos', ],
                                                key="gerenciar_opcao")
                            if aba2 == 'Mensalidade':
                                editar_status_mensalidade()
                            elif aba2 == 'Evento':
                                editar_status_inscricao()
                            elif aba2 == 'Débitos':
                                visualizar_debitos()

                        with st.expander('Inscrições'):
                            aba3 = st.selectbox("Esolha uma opção:", ['Increver no evento', 'Remover de um evento'])
                            if aba3 == 'Increver no evento':
                                inscrever_no_evento()
                            elif aba3 == 'Remover de um evento':
                                remover_inscricao()

                        with st.expander('Gerenciar eventos'):
                            aba4 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'])
                            if aba4 == 'Evento':
                                editar_evento()
                            if aba4 == 'Mensalidade':
                                editar_mensalidade()

                        with st.expander("Relatórios"):
                            visualizar_relatorios()

                        with st.expander("Caixa"):
                            gerenciar_caixa()

                        with st.expander("Fechamento"):
                            fechamento_mensal()
                    elif menu[i] == "Patrimonio":
                        gerenciar_patrimonio()

                    elif menu[i] == "Materiais":
                        sol()

                    elif menu[i] == "Atas e Atos":
                        atas_e_atos()

                    elif menu[i] == "Documentos":
                        docs()

                    elif menu[i] == 'Relatorios':
                        aba_extracao()

    else:
        st.sidebar.error("Incorrect Username/Password")


if __name__ == '__main__':
    main()
