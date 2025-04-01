import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, delete
from pgs.db import engine, tables


def criar_ata():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    reunioes = tables.get("reunioes")
    atas = tables.get("ata")

    if reunioes is None or atas is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Criar Ata de Reunião")

    with Session(engine) as session:
        reunioes_query = session.execute(select(reunioes.c.id, reunioes.c.nome, reunioes.c.data)).fetchall()

    if not reunioes_query:
        st.warning("⚠️ Nenhuma reunião cadastrada.")
        return

    reuniao_opcoes = {str(r.id): f"{r.nome} - {r.data}" for r in reunioes_query}
    reuniao_selecionada = st.selectbox("Selecione a Reunião", list(reuniao_opcoes.values()), key="select_reuniao_ata")
    reuniao_id = next(r for r in reuniao_opcoes if reuniao_opcoes[r] == reuniao_selecionada)

    titulo = st.text_input("Título da Ata")
    descricao = st.text_area("Descrição da Ata", key='nova_descr_ata')

    if st.button("💾 Salvar Ata", key="salvar_ata"):
        with Session(engine) as session:
            session.execute(insert(atas).values(reuniao_id=reuniao_id, titulo=titulo, descricao=descricao))
            session.commit()
        st.success("✅ Ata registrada com sucesso!")
        st.rerun()


def gerenciar_atas():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    atas = tables.get("ata")
    reunioes = tables.get("reunioes")

    if atas is None or reunioes is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Gerenciar Atas")

    with Session(engine) as session:
        atas_query = session.execute(
            select(atas.c.id, atas.c.titulo, atas.c.descricao, reunioes.c.nome, reunioes.c.data)
            .join(reunioes, atas.c.reuniao_id == reunioes.c.id)
            .order_by(reunioes.c.data.desc())
        ).fetchall()

    if not atas_query:
        st.info("📌 Nenhuma ata cadastrada.")
        return

    atas_opcoes = {str(a.id): f"{a.titulo} ({a.nome} - {a.data})" for a in atas_query}
    ata_selecionada = st.selectbox("Selecione a Ata para Gerenciar", list(atas_opcoes.values()), key="select_ata")
    ata_id = next(a for a in atas_opcoes if atas_opcoes[a] == ata_selecionada)

    ata_info = next(a for a in atas_query if str(a.id) == ata_id)
    novo_titulo = st.text_input("Título", ata_info.titulo)
    nova_descricao = st.text_area("Descrição", ata_info.descricao, key='edit_descr_area')

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Atualizar Ata", key="atualizar_ata"):
            with Session(engine) as session:
                session.execute(update(atas).where(atas.c.id == ata_id).values(titulo=novo_titulo, descricao=nova_descricao))
                session.commit()
            st.success("✅ Ata atualizada com sucesso!")
            st.rerun()

    with col2:
        if st.button("❌ Excluir Ata", key="deletar_ata"):
            with Session(engine) as session:
                session.execute(delete(atas).where(atas.c.id == ata_id))
                session.commit()
            st.warning("⚠️ Ata excluída!")
            st.rerun()


def criar_ato():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    atas = tables.get("ata")
    atos = tables.get("ato")
    unidades = tables.get("unidades")
    membros = tables.get("membros")

    if atas is None or atos is None or unidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Criar Ato para uma Unidade")

    with Session(engine) as session:
        atas_query = session.execute(select(atas.c.id, atas.c.titulo)).fetchall()

        unidade_usuario_query = session.execute(
            select(unidades.c.id, unidades.c.nome)
            .join(membros, membros.c.id_unidade == unidades.c.id)  # ✅ Faz o JOIN corretamente via id_unidade
            .where(membros.c.codigo_sgc == st.session_state.sgc)  # ✅ Filtra pelo código SGC do usuário logado
        ).fetchone()

    if not atas_query:
        st.warning("⚠️ Nenhuma ata cadastrada.")
        return

    if not unidade_usuario_query:
        st.error("⚠️ Você não tem uma unidade vinculada. Contate o administrador.")
        return

    atas_opcoes = {str(a.id): a.titulo for a in atas_query}
    ata_selecionada = st.selectbox("Selecione a Ata", list(atas_opcoes.values()), key="select_ata_ato")
    ata_id = next(a for a in atas_opcoes if atas_opcoes[a] == ata_selecionada)

    unidade_id, unidade_nome = unidade_usuario_query
    st.write(f"📌 Unidade: **{unidade_nome}**")

    titulo_ato = st.text_input("Título do Ato")
    descricao_ato = st.text_area("Descrição do Ato")

    if st.button("💾 Salvar Ato", key="salvar_ato"):
        with Session(engine) as session:
            session.execute(insert(atos).values(ata_id=ata_id, titulo=titulo_ato, descricao=descricao_ato, unidade_id=unidade_id))
            session.commit()
        st.success("✅ Ato registrado com sucesso!")
        st.rerun()


def gerenciar_atos():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    atos = tables.get("ato")
    atas = tables.get("ata")
    unidades = tables.get("unidades")

    if atos is None or atas is None or unidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Gerenciar Atos")

    with Session(engine) as session:
        atos_query = session.execute(
            select(atos.c.id, atos.c.titulo, atos.c.descricao, atas.c.titulo, unidades.c.nome)
            .join(atas, atos.c.ata_id == atas.c.id)
            .join(unidades, atos.c.unidade_id == unidades.c.id)
            .order_by(atas.c.titulo, unidades.c.nome)
        ).fetchall()

    if not atos_query:
        st.info("📌 Nenhum ato cadastrado.")
        return

    atos_opcoes = {str(a.id): f"{a.titulo} ({a[3]} - {a[4]})" for a in atos_query}
    ato_selecionado = st.selectbox("Selecione o Ato para Gerenciar", list(atos_opcoes.values()), key="select_ato")
    ato_id = next(a for a in atos_opcoes if atos_opcoes[a] == ato_selecionado)

    ato_info = next(a for a in atos_query if str(a.id) == ato_id)
    novo_titulo = st.text_input("Título", ato_info.titulo)
    nova_descricao = st.text_area("Descrição", ato_info.descricao)

    if st.button("💾 Atualizar Ato", key="atualizar_ato"):
        with Session(engine) as session:
            session.execute(update(atos).where(atos.c.id == ato_id).values(titulo=novo_titulo, descricao=nova_descricao))
            session.commit()
        st.success("✅ Ato atualizado!")
        st.rerun()


def atas_e_atos():
    st.subheader("📌 Gerenciamento de Atas e Atos")

    with st.expander("📜 Criar e Gerenciar Atas"):
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                criar_ata()
            with col2:
                gerenciar_atas()

    with st.expander("📑 Criar e Gerenciar Atos"):
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                criar_ato()
            with col2:
                gerenciar_atos()

