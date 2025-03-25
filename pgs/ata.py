import pandas as pd
import streamlit as st

from pgs.db import conect_db


def criar_ata():
    conn, c = conect_db()
    st.subheader("📌 Criar Ata de Reunião")

    # Buscar reuniões existentes
    reunioes = pd.read_sql("SELECT ID, nome, data FROM reunioes", conn)
    if reunioes.empty:
        st.warning("⚠️ Nenhuma reunião cadastrada. Cadastre uma reunião primeiro.")
        return

    # Selecionar reunião para vincular à ata
    reuniao_selecionada = st.selectbox(
        "Selecione a Reunião",
        reunioes.apply(lambda row: f"{row['nome']} - {row['data']}", axis=1),
        key="select_reuniao_ata"
    )

    # Obter ID da reunião selecionada
    reuniao_id = int(reunioes.loc[
        reunioes.apply(lambda row: f"{row['nome']} - {row['data']}", axis=1) == reuniao_selecionada, "id"
    ].values[0])
    titulo = st.text_input("Título da Ata")
    descricao = st.text_area("Descrição da Ata")

    if st.button("💾 Salvar Ata", key="salvar_ata"):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ata (reuniao_id, titulo, descricao) VALUES (%s, %s, %s)",
            (reuniao_id, titulo, descricao)
        )
        conn.commit()
        st.success("✅ Ata registrada com sucesso!")
        st.rerun()
    c.close()
    conn.close()


def gerenciar_atas():
    conn, c = conect_db()
    st.subheader("📌 Gerenciar Atas")

    # Buscar atas cadastradas
    atas = pd.read_sql("""
        SELECT a.id, a.titulo, a.descricao, r.nome as reuniao, r.data
        FROM ata a
        JOIN reunioes r ON a.reuniao_id = r.ID
        ORDER BY r.data DESC
    """, conn)

    if atas.empty:
        st.info("📌 Nenhuma ata cadastrada.")
        return

    # Selecionar ata para edição/exclusão
    ata_selecionada = st.selectbox(
        "Selecione a Ata para Gerenciar",
        atas.apply(lambda row: f"{row['titulo']} ({row['reuniao']} - {row['data']})", axis=1),
        key="select_ata"
    )

    # Obter ID da ata
    ata_id = atas.loc[
        atas.apply(lambda row: f"{row['titulo']} ({row['reuniao']} - {row['data']})", axis=1) == ata_selecionada, "id"
    ].values[0]

    # Campos editáveis
    novo_titulo = st.text_input("Título", atas.loc[atas["id"] == ata_id, "titulo"].values[0])
    nova_descricao = st.text_area("Descrição", atas.loc[atas["id"] == ata_id, "descricao"].values[0])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Atualizar Ata", key="atualizar_ata"):
            cursor = conn.cursor()
            cursor.execute("UPDATE ata SET titulo = %s, descricao = %s WHERE id = %s",
                           (novo_titulo, nova_descricao, ata_id))
            conn.commit()
            st.success("✅ Ata atualizada com sucesso!")
            st.rerun()

    with col2:
        if st.button("❌ Excluir Ata", key="deletar_ata"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ata WHERE id = %s", (ata_id,))
            conn.commit()
            st.warning("⚠️ Ata excluída!")
            st.rerun()
    c.close()
    conn.close()


def criar_ato():
    conn, c = conect_db()
    st.subheader("📌 Criar Ato para uma Unidade")

    # Buscar reuniões
    reunioes = pd.read_sql("SELECT ID, nome, data FROM reunioes", conn)
    if reunioes.empty:
        st.warning("⚠️ Nenhuma reunião cadastrada.")
        return

    # Selecionar reunião
    reuniao_selecionada = st.selectbox(
        "Selecione a Reunião",
        reunioes.apply(lambda row: f"{row['nome']} - {row['data']}", axis=1),
        key="select_reuniao_ato"
    )

    # Obter ID da reunião
    reuniao_id = int(reunioes.loc[
        reunioes.apply(lambda row: f"{row['nome']} - {row['data']}", axis=1) == reuniao_selecionada, "id"
    ].values[0])

    # Buscar atas dessa reunião
    atas = pd.read_sql("SELECT id, titulo FROM ata WHERE reuniao_id = %s", conn, params=[reuniao_id])

    if atas.empty:
        st.warning("⚠️ Nenhuma ata vinculada a essa reunião. Cadastre uma ata primeiro.")
        return

    # Selecionar ata
    ata_selecionada = st.selectbox("Selecione a Ata", atas["titulo"], key="select_ata_ato")
    ata_id = int(atas.loc[atas["titulo"] == ata_selecionada, "id"].values[0])

    # Buscar unidades
    query = """
        SELECT u.ID, u.nome 
        FROM membros m
        JOIN unidades u ON m.id_unidade = u.ID
        WHERE m.codigo_sgc = %s
    """
    unidade_usuario = pd.read_sql(query, conn, params=[st.session_state.sgc])

    if unidade_usuario.empty:
        st.error("⚠️ Você não tem uma unidade vinculada. Contate o administrador.")
    else:
        unidade_id = int(unidade_usuario["ID"].values[0])
        unidade_nome = unidade_usuario["nome"].values[0]

        # Exibir a unidade fixa, sem permitir alteração
        st.write(f"📌 Unidade: **{unidade_nome}**")

    titulo_ato = st.text_input("Título do Ato")
    descricao_ato = st.text_area("Descrição do Ato")

    if st.button("💾 Salvar Ato", key="salvar_ato"):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ato (ata_id, titulo, descricao, unidade_id) VALUES (%s, %s, %s, %s)",
            (ata_id, titulo_ato, descricao_ato, unidade_id)
        )
        conn.commit()
        st.success("✅ Ato registrado com sucesso!")
        st.rerun()
    c.close()
    conn.close()


def gerenciar_atos():
    conn, c = conect_db()
    st.subheader("📌 Gerenciar Atos")

    # Buscar atos cadastrados
    atos = pd.read_sql("""
        SELECT a.id, a.titulo, a.descricao, ata.titulo as ata_titulo, u.nome as unidade
        FROM ato a
        JOIN ata ON a.ata_id = ata.id
        JOIN unidades u ON a.unidade_id = u.ID
        ORDER BY ata.titulo, u.nome
    """, conn)

    if atos.empty:
        st.info("📌 Nenhum ato cadastrado.")
        return

    # Selecionar ato
    ato_selecionado = st.selectbox(
        "Selecione o Ato para Gerenciar",
        atos.apply(lambda row: f"{row['titulo']} ({row['ata_titulo']} - {row['unidade']})", axis=1),
        key="select_ato"
    )

    # Obter ID do ato
    ato_id = atos.loc[
        atos.apply(lambda row: f"{row['titulo']} ({row['ata_titulo']} - {row['unidade']})", axis=1) == ato_selecionado, "id"
    ].values[0]

    # Campos editáveis
    novo_titulo = st.text_input("Título", atos.loc[atos["id"] == ato_id, "titulo"].values[0])
    nova_descricao = st.text_area("Descrição", atos.loc[atos["id"] == ato_id, "descricao"].values[0])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Atualizar Ato", key="atualizar_ato"):
            cursor = conn.cursor()
            cursor.execute("UPDATE ato SET titulo = %s, descricao = %s WHERE id = %s", (novo_titulo, nova_descricao, ato_id))
            conn.commit()
            st.success("✅ Ato atualizado!")
            st.rerun()

    with col2:
        if st.button("❌ Excluir Ato", key="deletar_ato"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ato WHERE id = %s", (ato_id,))
            conn.commit()
            st.warning("⚠️ Ato excluído!")
            st.rerun()
    c.close()
    conn.close()

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

