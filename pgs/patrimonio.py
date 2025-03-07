import pandas as pd
import streamlit as st


def add_item(conn):
    st.subheader("➕ Adicionar Item ao Patrimônio")

    nome = st.text_input("Nome do Item")
    quantidade = st.number_input("Quantidade", min_value=1, value=1)
    descricao = st.text_area("Descrição (opcional)")
    data_aquisicao = st.date_input("Data de Aquisição")

    if st.button("Adicionar Item"):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO patrimonio (nome, quantidade, descricao, data_aquisicao)
            VALUES (?, ?, ?, ?)
        """, (nome, quantidade, descricao, data_aquisicao))

        conn.commit()
        st.success(f"✅ Item '{nome}' adicionado com sucesso!")
        st.rerun()


def view_items(conn):
    st.subheader("📋 Itens no Patrimônio")

    df = pd.read_sql("SELECT * FROM patrimonio ORDER BY nome", conn)

    if df.empty:
        st.info("📌 Nenhum item cadastrado no patrimônio.")
    else:
        st.dataframe(df)


def editar_remover_item(conn):
    st.subheader("✏️ Editar ou Remover Item do Patrimônio")

    # Buscar todos os itens cadastrados
    df = pd.read_sql("SELECT id, nome, quantidade, descricao, data_aquisicao FROM patrimonio", conn)

    if df.empty:
        st.warning("⚠️ Nenhum item encontrado para edição ou remoção.")
        return

    # Criar dicionário {Nome (ID) -> ID}
    item_dict = {f"{row['nome']} (ID {row['id']})": row['id'] for _, row in df.iterrows()}
    item_selecionado = st.selectbox("Selecione um item", list(item_dict.keys()))

    # Obter detalhes do item selecionado
    item_id = item_dict[item_selecionado]
    item_info = df[df["id"] == item_id].iloc[0]

    # Criar campos para edição
    novo_nome = st.text_input("Nome", item_info["nome"])
    nova_quantidade = st.number_input("Quantidade", min_value=0, value=item_info["quantidade"])
    nova_descricao = st.text_area("Descrição", item_info["descricao"])
    nova_data_aquisicao = st.date_input("Data de Aquisição", pd.to_datetime(item_info["data_aquisicao"]))

    # Criar colunas para botões
    col1, col2 = st.columns(2)

    # Botão para salvar alterações
    if col1.button("💾 Salvar Alterações", key=f"salvar_{item_id}"):
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE patrimonio 
            SET nome = ?, quantidade = ?, descricao = ?, data_aquisicao = ?
            WHERE id = ?
        """, (novo_nome, nova_quantidade, nova_descricao, nova_data_aquisicao, item_id))

        conn.commit()
        st.success(f"✅ Item '{novo_nome}' atualizado com sucesso!")
        st.rerun()

    # Botão para excluir item
    if col2.button("🗑️ Excluir Item", key=f"deletar_{item_id}"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patrimonio WHERE id = ?", (item_id,))
        conn.commit()

        st.warning(f"⚠️ Item '{item_info['nome']}' foi removido do patrimônio.")
        st.rerun()


def gerenciar_patrimonio(conn):
    st.title("🏛️ Gestão de Patrimônio")

    with st.expander("Adicionar"):
        add_item(conn)
    with st.expander("Visualizar"):
        view_items(conn)
    with st.expander("Editar"):
        editar_remover_item(conn)
