from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, insert
import pandas as pd
import streamlit as st
from pgs.db import get_db, engine, tables
import pandas as pd


def solicitar_item():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    patrimonio = tables.get("patrimonio")
    reunioes_table = tables.get("reunioes")
    solicitacoes_table = tables.get("solicitacoes")

    if patrimonio is None or reunioes_table is None or solicitacoes_table is None:
        st.error("❌ Tabelas necessárias não encontradas no banco de dados.")
        return

    st.subheader("📌 Solicitação de Materiais")

    with Session(engine) as session:
        itens = session.execute(select(patrimonio)).mappings().all()  # ✅ Retorna dicionários
        reunioes = session.execute(select(reunioes_table)).mappings().all()

    if not itens:
        st.warning("⚠️ Nenhum item disponível para solicitação.")
        return

    if not reunioes:
        st.warning("⚠️ Nenhuma reunião disponível.")
        return

    # Criar opções para seleção de reunião
    reuniao_dict = {row["nome"]: row["id"] for row in reunioes}
    reuniao_selecionada = st.selectbox("Reunião", list(reuniao_dict.keys()), key='reuniao')

    if not reuniao_selecionada:
        return

    reuniao_id = reuniao_dict[reuniao_selecionada]

    # Criar interface para solicitar materiais
    solicitacoes = {}
    for item in itens:
        item_nome = item["nome"]
        item_id = item["id"]
        max_qtd = item["quantidade"]

        qtd_solicitada = st.number_input(
            f"{item_nome} (Disponível: {max_qtd})", min_value=0, max_value=max_qtd, step=1,
            key=f"solicitacao_{item_id}"
        )

        if qtd_solicitada > 0:
            solicitacoes[item_id] = qtd_solicitada

    data_solicitacao = pd.Timestamp.now().date()

    if st.button("💾 Enviar Solicitação", key="enviar_solicitacao"):
        with Session(engine) as session:
            for item_id, qtd in solicitacoes.items():
                stmt = insert(solicitacoes_table).values(
                    codigo_sgc=st.session_state.get("sgc", "Desconhecido"),
                    id_item=item_id,
                    quantidade=qtd,
                    reuniao_id=reuniao_id,
                    data_solicitacao=data_solicitacao,
                    status="Pendente"
                )
                session.execute(stmt)

            session.commit()
            st.success("✅ Solicitação de materiais enviada!")
            st.rerun()


def gerenciar_solicitacoes():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    solicitacoes_table = tables.get("solicitacoes")
    membros_table = tables.get("membros")
    patrimonio_table = tables.get("patrimonio")

    if not solicitacoes_table or not membros_table or not patrimonio_table:
        st.error("❌ Tabelas necessárias não encontradas no banco de dados.")
        return

    st.subheader("📌 Gerenciar Solicitações Internas")

    with Session(engine) as session:
        query = select(
            solicitacoes_table.c.id,
            membros_table.c.nome.label("membro"),
            patrimonio_table.c.nome.label("item"),
            solicitacoes_table.c.quantidade,
            solicitacoes_table.c.data_solicitacao,
            solicitacoes_table.c.status
        ).join(membros_table, solicitacoes_table.c.codigo_sgc == membros_table.c.codigo_sgc
        ).join(patrimonio_table, solicitacoes_table.c.id_item == patrimonio_table.c.id
        ).order_by(solicitacoes_table.c.data_solicitacao.desc())

        df_solicitacoes = pd.DataFrame(session.execute(query).fetchall())

    if df_solicitacoes.empty:
        st.info("📌 Nenhuma solicitação pendente.")
        return

    # 🔹 Criando um identificador único no selectbox
    solicitacao_selecionada = st.selectbox(
        "Selecione uma Solicitação",
        df_solicitacoes.apply(lambda row: f"{row['id']} - {row['membro']} - {row['item']}", axis=1),
        key="select_solicitacao"
    )

    # 🔹 Obtendo os detalhes da solicitação
    sol_id = int(solicitacao_selecionada.split(" - ")[0])
    sol_info = df_solicitacoes[df_solicitacoes["id"] == sol_id].iloc[0]

    st.write(f"🔹 **Membro:** {sol_info['membro']}")
    st.write(f"📦 **Item Solicitado:** {sol_info['item']}")
    st.write(f"📆 **Data da Solicitação:** {sol_info['data_solicitacao']}")
    st.write(f"📊 **Quantidade:** {sol_info['quantidade']}")
    st.write(f"🔄 **Status Atual:** {sol_info['status']}")

    # 🔹 Atualização do status
    novo_status = st.selectbox(
        "Atualizar Status",
        ["Pendente", "Aprovado", "Negado"],
        index=["Pendente", "Aprovado", "Negado"].index(sol_info["status"]),
        key=f"status_{sol_id}"
    )

    col1, col2 = st.columns(2)

    if col1.button("💾 Atualizar Status", key=f"update_status_{sol_id}"):
        with Session(engine) as session:
            # Atualizar status da solicitação
            stmt = update(solicitacoes_table).where(solicitacoes_table.c.id == sol_id).values(status=novo_status)
            session.execute(stmt)

            # Se aprovado, diminuir estoque no patrimônio
            if novo_status == "Aprovado":
                stmt = update(patrimonio_table).where(
                    patrimonio_table.c.nome == sol_info["item"]
                ).values(
                    quantidade=patrimonio_table.c.quantidade - sol_info["quantidade"]
                )
                session.execute(stmt)

            session.commit()
            st.success(f"✅ Status atualizado para **{novo_status}**!")
            st.rerun()

    if col2.button("❌ Excluir Solicitação", key=f"delete_{sol_id}"):
        with Session(engine) as session:
            stmt = delete(solicitacoes_table).where(solicitacoes_table.c.id == sol_id)
            session.execute(stmt)
            session.commit()

        st.warning("⚠️ Solicitação excluída!")
        st.rerun()


def atualizar_status(codigo_sgc, reuniao_id, novo_status):
    """Atualiza o status das solicitações de um membro para uma reunião específica."""


    if not engine:
        raise Exception("Erro ao conectar ao banco de dados.")

    solicitacoes_table = tables.get("solicitacoes")

    if not solicitacoes_table:
        raise Exception("Tabela 'solicitacoes' não encontrada no banco de dados.")

    with Session(engine) as session:
        stmt = update(solicitacoes_table).where(
            (solicitacoes_table.c.codigo_sgc == codigo_sgc) &
            (solicitacoes_table.c.reuniao_id == reuniao_id)
        ).values(status=novo_status)

        session.execute(stmt)
        session.commit()


# Função card para exibir o conteúdo formatado e alterar o status
def card(title, content, codigo_sgc, reuniao_id, status_atual, color='white'):
    """
    Exibe um card estilo Trello e permite alterar o status do pedido.

    Arguments:
        title {str} -- Título do card
        content {str} -- Conteúdo do card
        codigo_sgc {int} -- Código SGC do pedido
        reuniao_id {int} -- ID da reunião
        status_atual {str} -- Status atual do pedido
        color {str} -- Cor de fundo do card (default: 'white')
    """

    # Estilos do card
    card_style = f"background-color: {color}; padding: 15px; border-radius: 10px; margin: 10px 0"
    title_style = "font-weight: bold; font-size: 20px; margin-bottom: 10px"
    content_style = "font-size: 16px"

    # Renderiza o card
    st.markdown(f"""
        <div style="{card_style}">
            <p style="{title_style}">{title}</p>
            <p style="{content_style}">{content}</p>
    """, unsafe_allow_html=True)

    # Status Dropdown
    status_opcoes = ["Pendente", "Emprestado", "Finalizado"]
    index_status = status_opcoes.index(status_atual) if status_atual in status_opcoes else 0
    novo_status = st.selectbox(f"Alterar Status", status_opcoes, index=index_status, key=f'{codigo_sgc}_{reuniao_id}_nst')

    # Botão de atualização
    if st.button(f"Alterar para {novo_status}", key=f'{codigo_sgc}_{reuniao_id}_bt'):
        if novo_status != status_atual:
            atualizar_status(codigo_sgc, reuniao_id, novo_status)  # Chamada correta da função
            st.success(f"✅ Status alterado para {novo_status}!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def gerenciar_solicitacoes_internas():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    # Obter tabelas
    reunioes = tables.get("reunioes")
    solicitacoes = tables.get("solicitacoes")
    membros = tables.get("membros")
    patrimonio = tables.get("patrimonio")

    if reunioes is None or solicitacoes is None or membros is None or patrimonio is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Gerenciar Solicitações Internas")

    with Session(engine) as session:
        # Buscar reuniões disponíveis
        reunioes_query = session.execute(select(reunioes.c.id, reunioes.c.nome)).fetchall()

    if not reunioes_query:
        st.warning("⚠️ Nenhuma reunião cadastrada.")
        return

    # Criar lista de reuniões para o selectbox
    reuniao_opcoes = {str(r.id): r.nome for r in reunioes_query}
    reuniao_selecionada = st.selectbox("Selecione uma Reunião", list(reuniao_opcoes.values()), key="select_reuniao")

    # Obter o ID da reunião selecionada
    reuniao_id = next(r for r in reuniao_opcoes if reuniao_opcoes[r] == reuniao_selecionada)

    with Session(engine) as session:
        # Buscar todas as solicitações para a reunião selecionada
        solicitacoes_query = session.execute(
            select(
                solicitacoes.c.id, solicitacoes.c.codigo_sgc, membros.c.nome,
                patrimonio.c.nome, solicitacoes.c.quantidade, solicitacoes.c.status
            )
            .join(membros, solicitacoes.c.codigo_sgc == membros.c.codigo_sgc)
            .join(patrimonio, solicitacoes.c.id_item == patrimonio.c.id)
            .where(solicitacoes.c.reuniao_id == reuniao_id)
            .order_by(solicitacoes.c.status.desc(), membros.c.nome)
        ).fetchall()

    if not solicitacoes_query:
        st.info("📌 Nenhuma solicitação encontrada para esta reunião.")
        return

    # Agrupar solicitações por membro
    agrupado = {}
    for sol in solicitacoes_query:
        key = (sol.codigo_sgc, sol.nome)  # Agrupar por código SGC e nome do membro
        if key not in agrupado:
            agrupado[key] = {"itens": {}, "status": sol.status}
        agrupado[key]["itens"][sol[3]] = sol.quantidade  # Nome do item como chave

    # Exibir os cards
    for (codigo_sgc, membro_nome), data in agrupado.items():
        descricao_itens = "<br>".join([f"{item}: {qtd}" for item, qtd in data["itens"].items()])

        card(
            title=f"Pedido de Itens - {codigo_sgc} - {membro_nome}",
            content=descricao_itens,
            codigo_sgc=codigo_sgc,
            reuniao_id=reuniao_id,
            status_atual=data["status"],
            color="lightblue"
        )


def sol():
    with st.expander("Interna"):
        solicitar_item()
    with st.expander("Gerenciar"):
        gerenciar_solicitacoes_internas()
