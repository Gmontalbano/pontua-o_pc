import pandas as pd
import streamlit as st


def solicitar_item(conn):
    st.subheader("📌 Solicitação de Materiais")

    # Buscar itens disponíveis no patrimônio
    itens = pd.read_sql("SELECT id, nome, quantidade FROM patrimonio", conn)
    if itens.empty:
        st.warning("⚠️ Nenhum item disponível para solicitação.")
        return

    # Criar dicionário para armazenar as seleções
    solicitacoes = {}
    reunioes = pd.read_sql("SELECT * FROM reunioes", conn)
    reuniao = st.selectbox("Reunião", reunioes['Nome'] if not reunioes.empty else [], key='Reunião_material')
    if reuniao:
        reuniao_id = int(reunioes[reunioes['Nome'] == reuniao]['ID'].values[0])
        # colunas
        # Criar interface para solicitar materiais
        for _, row in itens.iterrows():
            item_nome = row["nome"]
            item_id = row["id"]
            max_qtd = row["quantidade"]

            # Garantir que o `key` do `number_input` seja único
            qtd_solicitada = st.number_input(f"{item_nome} (Disponível: {max_qtd})", min_value=0, max_value=max_qtd, step=1,
                                             key=f"solicitacao_{item_id}")

            if qtd_solicitada > 0:
                solicitacoes[item_id] = qtd_solicitada
        data_solicitacao = pd.Timestamp.now().date()

        # Botão para salvar a solicitação
        if st.button("💾 Enviar Solicitação", key=f"enviar_solicitacao"):
            cursor = conn.cursor()
            for item_id, qtd in solicitacoes.items():
                cursor.execute("""
                    INSERT INTO solicitacoes (codigo_sgc, id_item, quantidade, reuniao_id, data_solicitacao, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (st.session_state.sgc, item_id, qtd, reuniao_id, data_solicitacao, 'Pendente'))

            conn.commit()
            st.success(f"✅ Solicitação de materiais enviada!")
            st.rerun()


def gerenciar_solicitacoes(conn):
    st.subheader("📌 Gerenciar Solicitações Internas")

    df_solicitacoes = pd.read_sql("""
        SELECT s.id, m.Nome AS membro, p.nome AS item, s.quantidade, s.data_solicitacao, s.status
        FROM solicitacoes s
        JOIN membros m ON s.codigo_sgc = m.codigo_sgc
        JOIN patrimonio p ON s.id_item = p.id
        ORDER BY s.data_solicitacao DESC
    """, conn)

    if df_solicitacoes.empty:
        st.info("📌 Nenhuma solicitação pendente.")
        return

    # 🔹 Criando um identificador único no selectbox
    solicitacao_selecionada = st.selectbox(
        "Selecione uma Solicitação",
        df_solicitacoes["id"].astype(str) + " - " + df_solicitacoes["membro"] + " - " + df_solicitacoes["item"],
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

    # 🔹 Adicionando um `key` único para evitar duplicação
    novo_status = st.selectbox(
        "Atualizar Status",
        ["Pendente", "Aprovado", "Negado"],
        index=["Pendente", "Aprovado", "Negado"].index(sol_info["status"]),
        key=f"status_{sol_id}"
    )

    col1, col2 = st.columns(2)

    if col1.button("💾 Atualizar Status", key=f"update_status_{sol_id}"):
        cursor = conn.cursor()

        # Atualizar status da solicitação
        cursor.execute("""
            UPDATE solicitacoes
            SET status = ?
            WHERE id = ?
        """, (novo_status, sol_id))

        # Se aprovado, diminuir estoque no patrimônio
        if novo_status == "Aprovado":
            cursor.execute("""
                UPDATE patrimonio
                SET quantidade = quantidade - ?
                WHERE nome = ?
            """, (sol_info["quantidade"], sol_info["item"]))

        conn.commit()
        st.success(f"✅ Status atualizado para **{novo_status}**!")
        st.rerun()

    if col2.button("❌ Excluir Solicitação", key=f"delete_{sol_id}"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM solicitacoes WHERE id = ?", (sol_id,))
        conn.commit()
        st.warning("⚠️ Solicitação excluída!")
        st.rerun()


# Função para atualizar o status no banco de dados
def atualizar_status(conn, codigo_sgc, reuniao_id, novo_status):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE solicitacoes
        SET status = ?
        WHERE codigo_sgc = ? AND reuniao_id = ?
    """, (novo_status, codigo_sgc, reuniao_id))
    conn.commit()

# Função card para exibir o conteúdo formatado e alterar o status
def card(conn, title, content, codigo_sgc, reuniao_id, status_atual, color='white'):
    """Exibe um card no estilo Trello e permite alterar o status do pedido.

    Arguments:
        conn {sqlite3.Connection} -- Conexão com o banco de dados
        title {str} -- Título do card
        content {str} -- Conteúdo do card
        codigo_sgc {int} -- Código SGC do pedido
        reuniao_id {int} -- ID da reunião
        status_atual {str} -- Status atual do pedido
        color {str} -- Cor de fundo do card (default: {'white'})

    Returns:
        None
    """
    card_style = f"background-color: {color}; padding: 10px; border-radius: 10px; margin: 10px 0"
    title_style = "font-weight: bold; font-size: 20px; margin-bottom: 10px"
    content_style = "font-size: 16px"

    # Exibe o card com os dados
    st.markdown(f"<div style='{card_style}'>", unsafe_allow_html=True)
    st.markdown(f"<p style='{title_style}'>{title}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='{content_style}'>{content}</p>", unsafe_allow_html=True)

    # Exibe o botão para alterar o status do pedido
    status_opcoes = ["Pendente", "Emprestado", "Finalizado"]

    # Encontrando o índice do status_atual na lista de opções
    index_status = status_opcoes.index(status_atual) if status_atual in status_opcoes else 0

    novo_status = st.selectbox(f"Alterar Status - {status_atual}", status_opcoes, index=index_status, key=f'{codigo_sgc}_{reuniao_id}_nst')


    # Quando o usuário seleciona um novo status, atualiza o banco de dados
    if st.button(f"Alterar para {novo_status}", key=f'{codigo_sgc}_{reuniao_id}_bt'):
        if novo_status and novo_status != status_atual:
            atualizar_status(conn, codigo_sgc, reuniao_id, novo_status)
            st.success(f"Status alterado para {novo_status}!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def gerenciar_solicitacoes_internas(conn):
    st.subheader("📌 Gerenciar Solicitações Internas")

    # Buscar todas as datas de solicitações únicas
    df_datas = pd.read_sql("SELECT DISTINCT data_solicitacao FROM solicitacoes", conn)

    if df_datas.empty:
        st.info("📌 Nenhuma solicitação encontrada.")
        return

    # Seleção da data
    reunioes = pd.read_sql("SELECT * FROM reunioes", conn)
    reuniao = st.selectbox("Reunião", reunioes['Nome'] if not reunioes.empty else [], key='Reunião_material_gerencia')
    if reuniao:
        reuniao_id = int(reunioes[reunioes['Nome'] == reuniao]['ID'].values[0])

        # Buscar solicitações da data selecionada
        df_solicitacoes = pd.read_sql("""
            SELECT 
        s.id, 
        s.codigo_sgc, 
        m.Nome AS membro_nome, 
        p.nome AS item_nome, 
        s.quantidade, 
        s.status, 
        r.Nome AS reuniao_nome,
        r.ID AS reuniao_id  -- Incluindo o ID da reunião
        FROM solicitacoes s
        JOIN membros m ON s.codigo_sgc = m.codigo_sgc
        JOIN patrimonio p ON s.id_item = p.id
        JOIN reunioes r ON s.reuniao_id = r.ID
        WHERE s.reuniao_id = ?
        ORDER BY s.status DESC, m.Nome
        """, conn, params=[reuniao_id])

        if df_solicitacoes.empty:
            st.info("📌 Nenhuma solicitação encontrada para esta data.")
            return
        else:
            df_agrupado = df_solicitacoes.groupby(['codigo_sgc', 'membro_nome', 'reuniao_nome', 'reuniao_id']).agg({
                'item_nome': lambda x: dict(zip(x, df_solicitacoes.loc[x.index, 'quantidade'])),
                # Criando o dicionário item_nome: quantidade
                'status': 'first'  # Retorna o primeiro status
            }).reset_index()

            # Loop para exibir os cards com as informações agrupadas
            for index, row in df_agrupado.iterrows():
                p = ""
                for item, qtd in row['item_nome'].items():
                    p += f"{item}: {qtd} <br>"

                # Exibindo o card com os itens e quantidades
                card(conn,
                     title=f"Pedido de Itens - {row['codigo_sgc']} - {row['membro_nome']} ({row['reuniao_nome']})",
                     content=p,
                     codigo_sgc=row['codigo_sgc'],
                     reuniao_id=row['reuniao_id'],  # Alterado para utilizar reuniao_id
                     status_atual=row['status'],
                     color="lightblue")


def sol(conn):
    with st.expander("Interna"):
        solicitar_item(conn)
    with st.expander("Gerenciar"):
        gerenciar_solicitacoes_internas(conn)
