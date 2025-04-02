import streamlit as st
from PIL import Image
import time
import streamlit.components.v1 as components
from utils.hashes import hash_senha
from pgs.db import engine, get_usuario

# Importação dos módulos do sistema
from pgs.cadastros import (cadastro_unidade, cadastro_reuniao, cadastro_especialidade, cadastro_classe,
                           delete_reuniao, cadastro_membro, delete_membro, gerenciar_usuarios)
from pgs.chamadas import registrar_chamada, visualizar_chamada
from pgs.pontuacao import show_pontos
from pgs.especialidades import mostrar_especialidades_usuario, gerenciar_especialidades_usuario
from pgs.classes import mostrar_classes_usuario, gerenciar_classes_usuario
from pgs.tesouraria import (criar_mensalidades, visualizar_relatorios, visualizar_debitos, editar_status_mensalidade,
                            criar_eventos, editar_status_inscricao, remover_inscricao, inscrever_no_evento,
                            editar_mensalidade, editar_evento, fechamento_mensal, gerenciar_caixa)
from pgs.patrimonio import gerenciar_patrimonio
from pgs.solicitacoes import sol
from pgs.ata import atas_e_atos
from pgs.documentos import docs
from pgs.extracao import aba_extracao

from pgs.db import engine, tables
from sqlalchemy.orm import Session
from sqlalchemy.sql import select

# Configuração da página
st.set_page_config(layout="wide", page_title="Pioneiros da Colina", page_icon='imgs/pc_logo.jpg', )

# **Definição do tempo limite para logout automático**
TIMEOUT_LOGOUT = 30  # Tempo em segundos


# **Função principal**
def main():
    # **Inicializa variáveis da sessão, se ainda não existirem**
    if "loggin" not in st.session_state:
        st.session_state.loggin = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_id" not in st.session_state:
        st.session_state.user_id = 0
    if "sgc" not in st.session_state:
        st.session_state.sgc = 0
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()  # Define o tempo inicial

    # **Atualiza a última atividade sempre que há uma interação**
    if st.session_state.get("loggin", False):
        st.session_state.last_activity = time.time()

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    # **Exibe a interface de login**
    img, title_text = st.columns([1, 8])
    image = Image.open('imgs/pc_logo.jpg')
    img.image(image, caption='Mais que um clube, uma família')
    title_text.title("Pioneiros da Colina")

    st.markdown(
        """
        <style>
            .footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                text-align: rigth;
                padding: 5px;
                font-size: 12px;
                color: #6c757d;
            }
        </style>
        <div class="footer">
            📌 Versão 1.1.11
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.title("Login Section")

    username = st.sidebar.text_input("User Name")
    password = st.sidebar.text_input("Password", type='password')

    botao = st.sidebar.button("Entrar")

    if botao or st.session_state.get("loggin", False):
        senha_hash = hash_senha(password)
        usuario = get_usuario(username, senha_hash)

        if usuario:
            nome = usuario["nome"]
            permissao_u = usuario["permissao"]
            sgc = usuario["codigo_sgc"]
            membros = tables.get("membros")
            permissao = tables.get("permissao")

            st.session_state.username = nome
            st.session_state.sgc = sgc
            st.session_state.loggin = True

            with Session(engine) as session:
                # Buscar permissões atuais do usuário no banco de dados
                user_permissoes = session.execute(
                    select(permissao.c.permissao).where(permissao.c.codigo_sgc == st.session_state.sgc)
                ).scalars().all()

                cargo_usuario = session.execute(
                    select(membros.c.cargo).where(membros.c.codigo_sgc == st.session_state.sgc)
                ).scalar()

            st.success(f"Bem-vindo, {nome}! {cargo_usuario} {sgc}")

            permissoes_disponiveis = ["Reuniões", "Membros", "Chamada",
                                      "Visualizar chamada", "Pontuação", "Usuário do sistema",
                                      "Especialidades", "Classes", "Tesouraria", "Patrimonio",
                                      "Materiais", "Atas e Atos", "Documentos", "Relatorios", "Novo"]

            user_permissoes_ordenadas = sorted(user_permissoes, key=lambda x: permissoes_disponiveis.index(x))

            menu = list(user_permissoes_ordenadas)

            # **Exibe as abas disponíveis conforme permissão do usuário**
            tabs = st.tabs(menu)
            for i, tab in enumerate(tabs):
                with tab:
                    if menu[i] == "Reuniões":
                        with st.expander("Cadastrar"):
                            cadastro_reuniao()
                        with st.expander("Editar"):
                            delete_reuniao()
                    elif menu[i] == "Membros":
                        with st.expander("Cadastrar"):
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
                        if cargo_usuario in ['Conselheiro', 'Diretor Associado', 'Selecione um cargo']:
                            mostrar_especialidades_usuario(st.session_state.sgc)
                            if cargo_usuario in ['Secretário', 'Selecione um cargo']:
                                gerenciar_especialidades_usuario()
                    elif menu[i] == "Classes":
                        if cargo_usuario in ['Conselheiro', 'Diretor Associado', 'Selecione um cargo']:
                            mostrar_classes_usuario(st.session_state.sgc)
                            if cargo_usuario in ['Secretário', 'Selecione um cargo']:
                                gerenciar_classes_usuario()
                    elif menu[i] == "Tesouraria":
                        with st.expander("Novo"):
                            aba1 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'], key="Tesouraria_novo")
                            if aba1 == 'Evento':
                                criar_eventos()
                            elif aba1 == 'Mensalidade':
                                criar_mensalidades()

                        with st.expander("Inscrição"):
                            inscrever_no_evento()
                            remover_inscricao()

                        with st.expander("Editar"):
                            aba2 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade'],
                                                key="Tesouraria_editar")
                            if aba2 == 'Evento':
                                editar_evento()
                            elif aba2 == 'Mensalidade':
                                editar_mensalidade()

                        with st.expander("Pagamentos"):
                            aba4 = st.selectbox("Escolha uma opção:", ['Evento', 'Mensalidade', 'Débitos'],
                                                key="Tesouraria_pagamentos")
                            if aba4 == 'Evento':
                                editar_status_inscricao()
                            elif aba4 == 'Mensalidade':
                                editar_status_mensalidade()
                            elif aba4 == 'Débitos':
                                visualizar_debitos()

                        with st.expander("Caixa"):
                            aba5 = st.selectbox("Escolha uma opção:", ['Relatório', 'Gerenciar', 'Fechamento'],
                                                key="Tesouraria_Caixa")
                            if aba5 == 'Relatório':
                                visualizar_relatorios()
                            elif aba5 == 'Gerenciar':
                                gerenciar_caixa()
                            elif aba5 == 'Fechamento':
                                fechamento_mensal()

                    elif menu[i] == "Patrimonio":
                        gerenciar_patrimonio()
                    elif menu[i] == "Materiais":
                        sol()
                    elif menu[i] == "Atas e Atos":
                        atas_e_atos()
                    elif menu[i] == "Documentos":
                        docs()
                    elif menu[i] == "Relatorios":
                        aba_extracao()
                    elif menu[i] == "Novo":
                        aba6 = st.selectbox("Escolha uma opção:", ['Especialidade', 'Classe', 'Unidade'],
                                            key="novo")
                        if aba6 == 'Especialidade':
                            cadastro_especialidade()
                        elif aba6 == 'Classe':
                            cadastro_classe()
                        elif aba6 == 'Unidade':
                            cadastro_unidade()

        else:
            st.sidebar.error("Usuário ou senha incorretos")


if __name__ == '__main__':
    main()
