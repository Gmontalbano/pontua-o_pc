import pandas as pd
import streamlit as st


def listar_eventos(conn):
    return pd.read_sql("SELECT id, nome FROM evento", conn)


def listar_documentos_evento(conn, id_evento):
    return pd.read_sql("SELECT id, nome_documento FROM evento_documentos WHERE id_evento = ?", conn,
                       params=(id_evento,))


def registrar_entrega(conn, codigo_sgc, id_evento, id_documento):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_evento_documentos (codigo_sgc, id_evento, id_documento) 
        VALUES (?, ?, ?)""", (codigo_sgc, id_evento, id_documento))
    conn.commit()


def listar_documentos_entregues(conn, id_evento):
    return pd.read_sql("""
        SELECT u.id, u.codigo_sgc, m.Nome AS membro, d.nome_documento, u.data_entrega 
        FROM user_evento_documentos u
        JOIN membros m ON u.codigo_sgc = m.codigo_sgc
        JOIN evento_documentos d ON u.id_documento = d.id
        WHERE u.id_evento = ?
    """, conn, params=(id_evento,))


def excluir_entrega(conn, id_registro):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_evento_documentos WHERE id = ?", (id_registro,))
    conn.commit()


def cadastrar_documento_evento(conn):
    st.subheader("📜 Cadastrar Documentos Necessários para Eventos")

    # Buscar eventos disponíveis
    eventos = pd.read_sql("SELECT id, nome FROM evento", conn)

    if eventos.empty:
        st.warning("Nenhum evento encontrado. Cadastre um evento antes de adicionar documentos.")
        return

    # Selecionar evento
    evento_nome = st.selectbox("Selecione o evento", eventos['Nome'])
    evento_id = int(eventos[eventos['Nome'] == evento_nome]['id'].values[0])

    # Campo para inserir o nome do documento
    nome_documento = st.text_input("Nome do Documento")

    if st.button("Cadastrar Documento"):
        if nome_documento.strip():
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evento_documentos (id_evento, nome_documento) 
                VALUES (?, ?)
            """, (evento_id, nome_documento))
            conn.commit()
            st.success(f"Documento '{nome_documento}' cadastrado com sucesso para o evento '{evento_nome}'!")
        else:
            st.error("O nome do documento não pode estar vazio.")


def docs(conn):
    st.title("📄 Gestão de Documentos de Eventos")

    cadastrar_documento_evento(conn)

    eventos = listar_eventos(conn)

    if eventos.empty:
        st.warning("Nenhum evento cadastrado.")
        return

    evento_selecionado = st.selectbox("Selecione um evento", eventos["Nome"].tolist())
    id_evento = int(eventos.loc[eventos["Nome"] == evento_selecionado, "id"].values[0])

    documentos = listar_documentos_evento(conn, id_evento)
    if documentos.empty:
        st.info("Nenhum documento cadastrado para este evento.")
    else:
        st.subheader("📜 Documentos Exigidos")
        st.table(documentos)

    st.subheader("📤 Registrar Entrega de Documento")
    membros = pd.read_sql("""
            SELECT membros.Nome, membros.codigo_sgc, unidades.Nome as Unidade 
            FROM membros 
            JOIN unidades ON membros.id_unidade = unidades.ID
        """, conn)

    membro_dict = {f"{row['Nome']} ({row['Unidade']})": row["codigo_sgc"] for _, row in membros.iterrows()}
    membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()), key='membro')

    membro_id = membro_dict[membro_selecionado]
    membro_info = membros[membros["codigo_sgc"] == membro_id].iloc[0]

    documento_selecionado = st.selectbox("Selecione o documento", documentos["nome_documento"].tolist(), key='doc')

    if st.button("Registrar Entrega"):
        id_documento = int(documentos.loc[documentos["nome_documento"] == documento_selecionado, "id"].values[0])
        registrar_entrega(conn, membro_info["codigo_sgc"], id_evento, id_documento)
        st.success("Entrega registrada com sucesso!")

    st.subheader("📂 Documentos Entregues")
    entregues = listar_documentos_entregues(conn, id_evento)
    if not entregues.empty:
        st.dataframe(entregues)
        id_excluir = st.selectbox("Selecione um registro para excluir", entregues["id"].tolist())
        if st.button("Excluir Registro"):
            excluir_entrega(conn, id_excluir)
            st.success("Registro excluído com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum documento entregue ainda.")

