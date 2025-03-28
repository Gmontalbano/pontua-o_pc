from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, delete
import streamlit as st
from pgs.db import engine, tables
import pandas as pd


def add_item():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    patrimonio = tables.get("patrimonio")

    if patrimonio is None:
        st.error("❌ A tabela 'patrimonio' não foi encontrada no banco de dados.")
        return

    st.subheader("➕ Adicionar Item ao Patrimônio")

    # 🔹 Campos do formulário
    nome = st.text_input("Nome do Item")
    quantidade = st.number_input("Quantidade", min_value=1, value=1)
    descricao = st.text_area("Descrição (opcional)")
    data_aquisicao = st.date_input("Data de Aquisição")

    # 🔹 Botão para adicionar item
    if st.button("Adicionar Item"):
        with Session(engine) as session:
            stmt = insert(patrimonio).values(
                nome=nome,
                quantidade=quantidade,
                descricao=descricao if descricao else None,  # Armazena None se descrição estiver vazia
                data_aquisicao=data_aquisicao
            )
            session.execute(stmt)
            session.commit()

        st.success(f"✅ Item '{nome}' adicionado com sucesso!")
        st.rerun()


def view_items():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    patrimonio = tables.get("patrimonio")

    if patrimonio is None:
        st.error("❌ A tabela 'patrimonio' não foi encontrada no banco de dados.")
        return

    st.subheader("📋 Itens no Patrimônio")

    with Session(engine) as session:
        result = session.execute(select(patrimonio).order_by(patrimonio.c.nome)).fetchall()

    if not result:
        st.info("📌 Nenhum item cadastrado no patrimônio.")
    else:
        df = pd.DataFrame(result, columns=patrimonio.c.keys())
        st.dataframe(df)


def editar_remover_item():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    patrimonio = tables.get("patrimonio")

    if patrimonio is None:
        st.error("❌ A tabela 'patrimonio' não foi encontrada no banco de dados.")
        return

    st.subheader("✏️ Editar ou Remover Item do Patrimônio")

    # Buscar todos os itens cadastrados
    with Session(engine) as session:
        result = session.execute(select(patrimonio)).fetchall()

    if not result:
        st.warning("⚠️ Nenhum item encontrado para edição ou remoção.")
        return

    df = pd.DataFrame(result, columns=patrimonio.c.keys())

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

    col1, col2 = st.columns(2)

    # Botão para salvar alterações
    if col1.button("💾 Salvar Alterações", key=f"salvar_{item_id}"):
        with Session(engine) as session:
            stmt = update(patrimonio).where(patrimonio.c.id == item_id).values(
                nome=novo_nome,
                quantidade=nova_quantidade,
                descricao=nova_descricao,
                data_aquisicao=nova_data_aquisicao
            )
            session.execute(stmt)
            session.commit()

        st.success(f"✅ Item '{novo_nome}' atualizado com sucesso!")
        st.rerun()

    # Botão para excluir item
    if col2.button("🗑️ Excluir Item", key=f"deletar_{item_id}"):
        with Session(engine) as session:
            stmt = delete(patrimonio).where(patrimonio.c.id == item_id)
            session.execute(stmt)
            session.commit()

        st.warning(f"⚠️ Item '{item_info['nome']}' foi removido do patrimônio.")
        st.rerun()


def gerenciar_patrimonio():
    st.title("🏛️ Gestão de Patrimônio")

    with st.expander("Adicionar"):
        add_item()
    with st.expander("Visualizar"):
        view_items()
    with st.expander("Editar"):
        editar_remover_item()
