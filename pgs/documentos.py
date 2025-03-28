import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, MetaData, select, insert, delete
from sqlalchemy.orm import Session
from pgs.db import get_db, engine, tables


def listar_eventos():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return pd.DataFrame()

    eventos = tables.get("evento")
    if eventos is None:
        st.error("❌ A tabela 'evento' não foi encontrada no banco de dados.")
        return pd.DataFrame()

    with Session(engine) as session:
        eventos_query = session.execute(select(eventos.c.id, eventos.c.nome)).fetchall()

    return pd.DataFrame(eventos_query, columns=["id", "nome"])



def listar_documentos_evento(id_evento):
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return pd.DataFrame()

    documentos = tables.get("evento_documentos")
    if documentos is None:
        st.error("❌ A tabela 'evento_documentos' não foi encontrada no banco de dados.")
        return pd.DataFrame()

    with Session(engine) as session:
        documentos_query = session.execute(
            select(documentos.c.id, documentos.c.nome_documento).where(documentos.c.id_evento == id_evento)
        ).fetchall()

    return pd.DataFrame(documentos_query, columns=["id", "nome_documento"])


def registrar_entrega(codigo_sgc, id_evento, id_documento):
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    entregas = tables.get("user_evento_documentos")
    if not entregas:
        st.error("❌ A tabela 'user_evento_documentos' não foi encontrada no banco de dados.")
        return

    with Session(engine) as session:
        session.execute(
            insert(entregas).values(
                codigo_sgc=codigo_sgc, id_evento=id_evento, id_documento=id_documento
            )
        )
        session.commit()

    st.success("✅ Entrega registrada com sucesso!")



def listar_documentos_entregues(id_evento):
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return pd.DataFrame()

    entregas = tables.get("user_evento_documentos")
    membros = tables.get("membros")
    documentos = tables.get("evento_documentos")

    if entregas is None or membros is None or documentos is None:
        st.error("❌ Algumas tabelas necessárias não foram encontradas no banco de dados.")
        return pd.DataFrame()

    with Session(engine) as session:
        entregas_query = session.execute(
            select(
                entregas.c.id, entregas.c.codigo_sgc, membros.c.nome,
                documentos.c.nome_documento, entregas.c.data_entrega
            )
            .join(membros, entregas.c.codigo_sgc == membros.c.codigo_sgc)
            .join(documentos, entregas.c.id_documento == documentos.c.id)
            .where(entregas.c.id_evento == id_evento)
        ).fetchall()

    return pd.DataFrame(entregas_query, columns=["id", "codigo_sgc", "membro", "nome_documento", "data_entrega"])


def excluir_entrega(id_registro):
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    entregas = tables.get("user_evento_documentos")
    if not entregas:
        st.error("❌ A tabela 'user_evento_documentos' não foi encontrada no banco de dados.")
        return

    with Session(engine) as session:
        session.execute(delete(entregas).where(entregas.c.id == id_registro))
        session.commit()

    st.warning("⚠️ Registro excluído com sucesso!")


def cadastrar_documento_evento():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    eventos = tables.get("evento")
    documentos = tables.get("evento_documentos")

    if eventos is None or documentos is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📜 Cadastrar Documentos Necessários para Eventos")

    with Session(engine) as session:
        eventos_query = session.execute(select(eventos.c.id, eventos.c.nome)).fetchall()

    if not eventos_query:
        st.warning("Nenhum evento encontrado. Cadastre um evento antes de adicionar documentos.")
        return

    eventos_opcoes = {str(e.id): e.nome for e in eventos_query}
    evento_selecionado = st.selectbox("Selecione o evento", list(eventos_opcoes.values()))
    evento_id = next(e for e in eventos_opcoes if eventos_opcoes[e] == evento_selecionado)

    nome_documento = st.text_input("Nome do Documento")

    if st.button("Cadastrar Documento"):
        if nome_documento.strip():
            with Session(engine) as session:
                session.execute(
                    insert(documentos).values(id_evento=evento_id, nome_documento=nome_documento)
                )
                session.commit()
            st.success(f"Documento '{nome_documento}' cadastrado com sucesso para o evento '{evento_selecionado}'!")
        else:
            st.error("O nome do documento não pode estar vazio.")



def docs():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    st.title("📄 Gestão de Documentos de Eventos")

    cadastrar_documento_evento()

    eventos = listar_eventos()

    if eventos.empty:
        st.warning("Nenhum evento cadastrado.")
        return
    membros = tables.get("membros")
    unidades = tables.get("unidades")
    if membros is None or unidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    evento_selecionado = st.selectbox("Selecione um evento", eventos["nome"].tolist())
    id_evento = int(eventos.loc[eventos["nome"] == evento_selecionado, "id"].values[0])

    documentos = listar_documentos_evento(id_evento)
    if documentos.empty:
        st.info("Nenhum documento cadastrado para este evento.")
    else:
        st.subheader("📜 Documentos Exigidos")
        st.table(documentos)

    st.subheader("📤 Registrar Entrega de Documento")
    with Session(engine) as session:
        membros_query = session.execute(
            select(membros.c.nome, membros.c.codigo_sgc, unidades.c.nome)
            .join(unidades, membros.c.id_unidade == unidades.c.id)
        ).fetchall()

    if not membros_query:
        st.warning("Nenhum membro encontrado.")
        return

    membro_dict = {f"{row.nome} ({row[2]})": row.codigo_sgc for row in membros_query}
    membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()), key='membro')
    membro_id = membro_dict[membro_selecionado]

    documento_selecionado = st.selectbox("Selecione o documento", documentos["nome_documento"].tolist())

    if st.button("Registrar Entrega"):
        id_documento = int(documentos.loc[documentos["nome_documento"] == documento_selecionado, "id"].values[0])
        registrar_entrega(membro_id, id_evento, id_documento)

    st.subheader("📂 Documentos Entregues")
    entregues = listar_documentos_entregues(id_evento)
    if not entregues.empty:
        st.dataframe(entregues)
        id_excluir = st.selectbox("Selecione um registro para excluir", entregues["id"].tolist())
        if st.button("Excluir Registro"):
            excluir_entrega(id_excluir)
            st.rerun()
    else:
        st.info("Nenhum documento entregue ainda.")


