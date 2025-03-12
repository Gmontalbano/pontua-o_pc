import pandas as pd
import streamlit as st
from datetime import datetime
from pgs.db import conect_db

def criar_mensalidades():
    conn, c = conect_db()
    st.subheader("📌 Criar Mensalidades")

    # Entrada de dados para a mensalidade
    ano = st.number_input("Ano", min_value=2024, max_value=2100, value=datetime.now().year, step=1)
    valor = st.number_input("Valor da Mensalidade", min_value=0.0, format="%.2f")

    if st.button("💾 Criar Mensalidades do Ano"):
        cursor = conn.cursor()

        # Criar mensalidades para os 12 meses do ano selecionado
        for mes in range(1, 13):
            cursor.execute("INSERT INTO mensalidades (valor, ano, mes) VALUES (%s,%s,%s)", (valor, ano, mes))

            # Recuperar o ID da mensalidade recém-criada
            id_mensalidade = cursor.lastrowid

            # Buscar todos os membros com cargo "Desbravador(a)"
            membros = cursor.execute(
                "SELECT codigo_sgc FROM membros WHERE cargo = 'Desbravador(a)'"
            ).fetchall()

            # Explodir mensalidade para todos os desbravadores
            for membro in membros:
                cursor.execute(
                    "INSERT INTO user_mensalidades (id_mensalidade, codigo_sgc, status) VALUES (%s, %s, %s)",
                    (id_mensalidade, membro[0], "Pendente")
                )

        conn.commit()
        st.success("✅ Mensalidades criadas para os 12 meses e atribuídas aos desbravadores!")
        c.close()
        conn.close()


def criar_eventos():
    conn, c = conect_db()
    st.subheader("📌 Criar Eventos")

    nome_evento = st.text_input("Nome do Evento")
    valor_evento = st.number_input("Valor do evento", min_value=0.0, format="%.2f")

    if st.button("💾 Criar Evento"):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO evento (Nome, valor) VALUES (%s, %s)",
                       (nome_evento, valor_evento))
        conn.commit()
        st.success(f"✅ Evento '{nome_evento}' criado com sucesso!")
    c.close()
    conn.close()


def inscrever_no_evento():
    conn, c = conect_db()
    st.subheader("📌 Inscrever em Evento")

    # Buscar eventos disponíveis
    eventos = pd.read_sql("SELECT id, nome FROM evento", conn)
    if eventos.empty:
        st.warning("⚠️ Nenhum evento encontrado. Cadastre um evento antes de inscrever participantes.")
        return

    # Selecionar evento
    evento_selecionado = st.selectbox("Selecione um Evento", eventos["nome"], key="select_evento")
    evento_id = eventos.loc[eventos["nome"] == evento_selecionado, "id"].values[0]

    # Buscar membros (desbravadores)
    membros = pd.read_sql("SELECT codigo_sgc, nome FROM membros ", conn)
    if membros.empty:
        st.warning("⚠️ Nenhum desbravador encontrado para inscrição.")
        return

    # Criar coluna formatada para exibir "Código SGC - Nome"
    membros["display"] = membros["codigo_sgc"] + " - " + membros["nome"]

    # Selecionar o membro no formato desejado
    membro_selecionado = st.selectbox("Selecione um Desbravador", membros["display"], key="select_membro")

    # Obter o código SGC real a partir da seleção
    codigo_sgc = membros.loc[membros["display"] == membro_selecionado, "codigo_sgc"].values[0]
    evento_id = int(evento_id)
    if st.button("💾 Inscrever"):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO inscricao_eventos (codigo_sgc, id_evento, status) VALUES (%s, %s, 'Pendente')",
                       (codigo_sgc, evento_id))
        conn.commit()
        st.success(f"✅ {membro_selecionado} foi inscrito no evento '{evento_selecionado}'!")
        st.rerun()
    c.close()
    conn.close()


def editar_status_inscricao():
    conn, c = conect_db()
    st.subheader("✏️ Editar Status de Pagamento")

    # Buscar eventos existentes
    eventos = pd.read_sql("SELECT id, nome, valor FROM evento", conn)
    if eventos.empty:
        st.warning("⚠️ Nenhum evento encontrado.")
        return

    # Selecionar um evento
    evento_selecionado = st.selectbox(
        "Selecione um Evento",
        eventos["nome"],
        key="editar_evento"
    )

    # Obter ID e valor do evento selecionado
    evento_id = int(eventos.loc[eventos["nome"] == evento_selecionado, "id"].values[0])
    valor_evento = float(eventos.loc[eventos["id"] == evento_id, "valor"].values[0])

    st.write(f"💰 **Valor do Evento:** R$ {valor_evento:.2f}")

    # Buscar inscritos no evento
    inscritos = pd.read_sql("""
        SELECT ie.codigo_sgc, m.nome, ie.status 
        FROM inscricao_eventos ie
        JOIN membros m ON ie.codigo_sgc = m.codigo_sgc
        WHERE ie.id_evento = %s
    """, conn, params=[evento_id])

    if inscritos.empty:
        st.info("📌 Nenhum desbravador está inscrito neste evento.")
        return

    # Criar coluna "Código SGC - Nome" para exibição
    inscritos["display"] = inscritos["codigo_sgc"] + " - " + inscritos["nome"]

    # Selecionar um inscrito para edição
    inscrito_selecionado = st.selectbox("Selecione um Desbravador", inscritos["display"], key=f"inscrito_{evento_id}")

    # Obter o código SGC do inscrito selecionado
    codigo_sgc = inscritos.loc[inscritos["display"] == inscrito_selecionado, "codigo_sgc"].values[0]

    # Obter status atual do inscrito
    status_atual = inscritos.loc[inscritos["display"] == inscrito_selecionado, "status"].values[0]

    # Criar selectbox para editar status
    novo_status = st.selectbox(
        "Status:",
        ["Pendente", "Pago", "Cancelado"],
        index=["Pendente", "Pago", "Cancelado"].index(status_atual),
        key=f"status_{codigo_sgc}_{evento_id}"
    )

    # Botão para atualizar status
    if st.button("💾 Atualizar Status", key=f"atualizar_status_evento_{evento_id}"):
        cursor = conn.cursor()

        # Apenas atualizar se houve mudança no status
        if status_atual != novo_status:
            cursor.execute("""
                UPDATE inscricao_eventos 
                SET status = %s 
                WHERE id_evento = %s AND codigo_sgc = %s
            """, (novo_status, evento_id, codigo_sgc))

            # Se mudou de "Pendente" ou "Cancelado" para "Pago", registrar no caixa
            if novo_status == "Pago" and status_atual != "Pago":
                descricao = f"Evento {evento_selecionado} - {codigo_sgc}"
                data_hoje = pd.Timestamp.today().strftime("%Y-%m-%d")

                cursor.execute("""
                    INSERT INTO caixa (tipo, descricao, valor, data, id_evento) 
                    VALUES ('Entrada', %s, %s, %s, %s)
                """, (descricao, valor_evento, data_hoje, evento_id))  # 🔹 Agora salva o ID do evento!

        conn.commit()
        st.success(f"✅ Status atualizado com sucesso para {inscrito_selecionado}!")
        st.rerun()
    c.close()
    conn.close()


def remover_inscricao():
    conn, c = conect_db()
    st.subheader("🗑️ Remover Inscrição")

    # Buscar eventos disponíveis
    eventos = pd.read_sql("SELECT id, nome FROM evento", conn)
    if eventos.empty:
        st.warning("⚠️ Nenhum evento encontrado.")
        return

    # Selecionar evento
    evento_selecionado = st.selectbox("Selecione um Evento", eventos["nome"], key="remover_evento")
    evento_id = eventos.loc[eventos["nome"] == evento_selecionado, "id"].values[0]

    # Buscar inscritos no evento
    inscritos = pd.read_sql("""
        SELECT ie.codigo_sgc, m.nome 
        FROM inscricao_eventos ie
        JOIN membros m ON ie.codigo_sgc = m.codigo_sgc
        WHERE ie.id_evento = %s
    """, conn, params=[evento_id])

    if inscritos.empty:
        st.info("📌 Nenhum desbravador está inscrito neste evento.")
        return

    # Selecionar inscrito para remover
    inscrito_selecionado = st.selectbox("Selecione um Desbravador para remover", inscritos["nome"], key="select_remover")
    codigo_sgc = inscritos.loc[inscritos["nome"] == inscrito_selecionado, "codigo_sgc"].values[0]

    if st.button("❌ Remover Inscrição", key="remover_inscricao"):
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM inscricao_eventos 
            WHERE id_evento = %s AND codigo_sgc = %s
        """, (evento_id, codigo_sgc))

        conn.commit()
        st.warning(f"⚠️ {inscrito_selecionado} foi removido do evento '{evento_selecionado}'.")
        st.rerun()
    c.close()
    conn.close()


def visualizar_relatorios():
    conn, c = conect_db()
    st.subheader("📊 Relatórios Financeiros")

    # 🔹 Visão Geral por Ano (Usando a tabela de fechamento)
    st.subheader("📆 Visão Geral por Ano")
    df_ano = pd.read_sql("""
        SELECT ano, 
               SUM(entrada) as total_entradas, 
               SUM(saida) as total_saidas
        FROM fechamento
        GROUP BY ano
        ORDER BY ano DESC
    """, conn)

    if not df_ano.empty:
        st.dataframe(df_ano)
    else:
        st.info("📌 Nenhum dado encontrado para a visão anual.")

    # 🔹 Visão Geral por Mês (Usando a tabela de fechamento)
    st.subheader("📅 Visão Geral por Mês")
    df_mes = pd.read_sql("""
        SELECT ano, mes, entrada as total_entradas, saida as total_saidas
        FROM fechamento
        ORDER BY ano DESC, mes DESC
    """, conn)

    if not df_mes.empty:
        df_mes["Mês/Ano"] = df_mes["mes"].astype(str) + "/" + df_mes["ano"].astype(str)
        df_mes = df_mes[["Mês/Ano", "total_entradas", "total_saidas"]]
        st.dataframe(df_mes)
    else:
        st.info("📌 Nenhum dado encontrado para a visão mensal.")

    # 🔹 Filtros Específicos
    st.subheader("🎯 Eventos")

    # Buscar eventos com movimentações no caixa
    eventos = pd.read_sql("""
        SELECT DISTINCT e.id, e.nome 
        FROM evento e
        JOIN caixa c ON e.id = c.id_evento
    """, conn)

    if not eventos.empty:
        # Criar dicionário de eventos para exibição
        evento_dict = {f"{row['nome']}": row["id"] for _, row in eventos.iterrows()}
        evento_selecionado = st.selectbox("Selecione um Evento ou Mensalidade", list(evento_dict.keys()))

        # Obter o ID real do evento selecionado
        id_evento = evento_dict[evento_selecionado]

        # Buscar entradas e saídas relacionadas ao evento
        df_evento = pd.read_sql("""
            SELECT data, tipo, descricao, valor
            FROM caixa
            WHERE id_evento = %s
            ORDER BY data DESC
        """, conn, params=[id_evento])

        if not df_evento.empty:
            # Separar entradas e saídas
            total_entradas = df_evento[df_evento["tipo"] == "Entrada"]["valor"].sum()
            total_saidas = df_evento[df_evento["tipo"] == "Saída"]["valor"].sum()
            saldo_evento = total_entradas - total_saidas

            st.write(f"📥 **Total Entradas:** R$ {total_entradas:.2f}")
            st.write(f"📤 **Total Saídas:** R$ {total_saidas:.2f}")
            st.write(f"💰 **Saldo do Evento:** R$ {saldo_evento:.2f}")

            # Exibir dataframe com os detalhes das movimentações
            st.dataframe(df_evento)
        else:
            st.info("📌 Nenhuma movimentação registrada para este evento.")

    else:
        st.warning("⚠️ Nenhum evento com movimentação financeira encontrado.")

    # 🔹 Cálculo do Caixa e Custos
    st.subheader("💰 Cálculo do Caixa e Custos")
    df_total = pd.read_sql("""
        SELECT SUM(entrada) as total_entradas,
               SUM(saida) as total_saidas
        FROM fechamento
    """, conn)

    total_entradas = df_total["total_entradas"].values[0] if df_total["total_entradas"].values[0] else 0
    total_saidas = df_total["total_saidas"].values[0] if df_total["total_saidas"].values[0] else 0
    saldo_final = total_entradas - total_saidas

    st.write(f"📥 **Total de Entradas:** R$ {total_entradas:.2f}")
    st.write(f"📤 **Total de Saídas:** R$ {total_saidas:.2f}")
    st.write(f"💵 **Saldo Final:** R$ {saldo_final:.2f}")

    # 🔹 Indicadores no Relatório
    st.subheader("📊 Indicadores de Mensalidades")

    df_mensalidades = pd.read_sql("""
        SELECT um.status, COUNT(*) as total_mensalidades, COUNT(DISTINCT um.codigo_sgc) as total_usuarios
        FROM user_mensalidades um
        GROUP BY um.status
    """, conn)

    if not df_mensalidades.empty:
        # Exibir contagem específica de mensalidades
        em_dia = df_mensalidades[df_mensalidades["status"] == "Pago"]["total_mensalidades"].sum() if "Pago" in \
                                                                                                     df_mensalidades[
                                                                                                         "status"].values else 0
        atrasados = df_mensalidades[df_mensalidades["status"] == "Pendente"][
            "total_mensalidades"].sum() if "Pendente" in df_mensalidades["status"].values else 0
        isentos = df_mensalidades[df_mensalidades["status"] == "Isento"]["total_mensalidades"].sum() if "Isento" in \
                                                                                                        df_mensalidades[
                                                                                                            "status"].values else 0

        # Exibir contagem específica de usuários únicos
        em_dia_users = df_mensalidades[df_mensalidades["status"] == "Pago"]["total_usuarios"].sum() if "Pago" in \
                                                                                                       df_mensalidades[
                                                                                                           "status"].values else 0
        atrasados_users = df_mensalidades[df_mensalidades["status"] == "Pendente"][
            "total_usuarios"].sum() if "Pendente" in df_mensalidades["status"].values else 0
        isentos_users = df_mensalidades[df_mensalidades["status"] == "Isento"]["total_usuarios"].sum() if "Isento" in \
                                                                                                          df_mensalidades[
                                                                                                              "status"].values else 0

        st.write(f"✅ **Mensalidades pagas:** {em_dia} - {em_dia_users} usuários")
        st.write(f"⚠️ **Mensalidades em aberto:** {atrasados} - {atrasados_users} usuários")
        st.write(f"🆓 **Mensalidades isentas:** {isentos} - {isentos_users} usuários")
    else:
        st.info("📌 Nenhum dado encontrado para o período total.")

    st.subheader("📊 Mensalidades detalhadas")

    anos = pd.read_sql("SELECT DISTINCT ano FROM mensalidades ORDER BY ano DESC", conn)
    if not anos.empty:
        ano_selecionado = st.selectbox("Selecione o Ano", anos["ano"])

        meses = pd.read_sql("SELECT DISTINCT mes FROM mensalidades WHERE ano = %s ORDER BY mes ASC", conn,
                            params=[ano_selecionado])
        if not meses.empty:
            mes_selecionado = st.selectbox("Selecione o Mês", meses["mes"])

            df_mensalidades = pd.read_sql("""
                SELECT um.status, COUNT(*) as total_mensalidades, COUNT(DISTINCT um.codigo_sgc) as total_usuarios
                FROM user_mensalidades um
                JOIN mensalidades m ON um.id_mensalidade = m.id
                WHERE m.ano = %s AND m.mes = %s
                GROUP BY um.status
            """, conn, params=[ano_selecionado, mes_selecionado])

            if not df_mensalidades.empty:
                # Exibir contagem específica de mensalidades
                em_dia = df_mensalidades[df_mensalidades["status"] == "Pago"]["total_mensalidades"].sum() if "Pago" in \
                                                                                                             df_mensalidades[
                                                                                                                 "status"].values else 0
                atrasados = df_mensalidades[df_mensalidades["status"] == "Pendente"][
                    "total_mensalidades"].sum() if "Pendente" in df_mensalidades["status"].values else 0
                isentos = df_mensalidades[df_mensalidades["status"] == "Isento"][
                    "total_mensalidades"].sum() if "Isento" in df_mensalidades["status"].values else 0

                # Exibir contagem específica de usuários únicos
                em_dia_users = df_mensalidades[df_mensalidades["status"] == "Pago"]["total_usuarios"].sum() if "Pago" in \
                                                                                                               df_mensalidades[
                                                                                                                   "status"].values else 0
                atrasados_users = df_mensalidades[df_mensalidades["status"] == "Pendente"][
                    "total_usuarios"].sum() if "Pendente" in df_mensalidades["status"].values else 0
                isentos_users = df_mensalidades[df_mensalidades["status"] == "Isento"][
                    "total_usuarios"].sum() if "Isento" in df_mensalidades["status"].values else 0

                st.write(f"✅ **Mensalidades pagas:** {em_dia} - {em_dia_users} usuários")
                st.write(f"⚠️ **Mensalidades em aberto:** {atrasados} - {atrasados_users} usuários")
                st.write(f"🆓 **Mensalidades isentas:** {isentos} - {isentos_users} usuários")
            else:
                st.info("📌 Nenhum dado encontrado para o período selecionado.")

        else:
            st.info("📌 Nenhum dado encontrado para este ano.")

    else:
        st.warning("⚠️ Nenhum dado encontrado na tabela de mensalidades.")
    c.close()
    conn.close()


def editar_status_mensalidade():
    conn, c = conect_db()
    st.subheader("✏️ Editar Status de Pagamento")

    # Buscar todos os desbravadores com mensalidades
    desbravadores = pd.read_sql("""
        SELECT DISTINCT m.codigo_sgc, m.nome
        FROM membros m
        JOIN user_mensalidades um ON m.codigo_sgc = um.codigo_sgc
        WHERE m.cargo = 'Desbravador(a)'
        ORDER BY m.nome
    """, conn)

    if desbravadores.empty:
        st.warning("⚠️ Nenhum desbravador encontrado com mensalidades registradas.")
        return

    # Criar selectbox formatado como "Código SGC - nome"
    desbravadores["display"] = desbravadores["codigo_sgc"] + " - " + desbravadores["nome"]

    # Selecionar o desbravador
    desbravador_selecionado = st.selectbox("Selecione um Desbravador", desbravadores["display"])

    # Obter o código SGC real do desbravador selecionado
    codigo_sgc = desbravadores.loc[desbravadores["display"] == desbravador_selecionado, "codigo_sgc"].values[0]

    # Buscar mensalidades do desbravador
    mensalidades = pd.read_sql("""
        SELECT um.id_mensalidade, um.status AS status_atual, m.ano, m.mes, m.valor
        FROM user_mensalidades um
        JOIN mensalidades m ON um.id_mensalidade = m.id
        WHERE um.codigo_sgc = %s
        ORDER BY m.ano, m.mes
    """, conn, params=[codigo_sgc])

    if mensalidades.empty:
        st.info("📌 Este desbravador não tem mensalidades registradas.")
        return

    # Criar dicionário para armazenar mudanças de status
    novos_status = {}

    col1, col2, col3 = st.columns(3)
    colunas = [col1, col2, col3]
    i = 0

    for _, row in mensalidades.iterrows():
        with colunas[i]:  # Alterna entre as colunas para melhor visualização
            id_mensalidade = row["id_mensalidade"]
            ano = row["ano"]
            mes = row["mes"]
            valor = row["valor"]
            status_atual = row["status_atual"]

            # Criar selectbox com a opção de status
            novo_status = st.selectbox(
                f"📆 {mes}/{ano} - R$ {valor:.2f}",
                ["Pendente", "Pago", "Isento"],
                index=["Pendente", "Pago", "Isento"].index(status_atual),
                key=f"status_{id_mensalidade}_{codigo_sgc}"
            )

            # Armazena o status antigo e o novo
            novos_status[id_mensalidade] = (status_atual, novo_status, valor)
            i = (i + 1) % 3  # Alternar entre as colunas

    # Botão para salvar alterações
    if st.button("💾 Atualizar Status", key="atualizar_status"):
        cursor = conn.cursor()

        for id_mensalidade, (status_atual, novo_status, valor) in novos_status.items():
            # Apenas atualiza se houver mudança
            if status_atual != novo_status:
                cursor.execute("""
                    UPDATE user_mensalidades 
                    SET status = %s 
                    WHERE id_mensalidade = %s AND codigo_sgc = %s
                """, (novo_status, id_mensalidade, codigo_sgc))

                # Se mudou de "Pendente" ou "Isento" para "Pago", registrar no caixa
                if novo_status == "Pago" and status_atual != "Pago":
                    descricao = f"Mensalidade - {codigo_sgc}"
                    data_hoje = pd.Timestamp.today().strftime("%Y-%m-%d")

                    cursor.execute("""
                        INSERT INTO caixa (tipo, descricao, valor, data) 
                        VALUES ('Entrada', %s, %s, %s)
                    """, (descricao, valor, data_hoje))

        conn.commit()
        st.success("✅ Status atualizado com sucesso!")
        st.rerun()
    c.close()
    conn.close()


def visualizar_debitos():
    conn, c = conect_db()
    st.subheader("💰 Débitos dos Desbravadores")

    # Buscar desbravadores que possuem mensalidades ou eventos pendentes
    membros = pd.read_sql("""
        SELECT DISTINCT m.codigo_sgc, m.nome 
        FROM membros m
        LEFT JOIN user_mensalidades um ON um.codigo_sgc = m.codigo_sgc AND um.status = 'Pendente'
        LEFT JOIN inscricao_eventos ie ON ie.codigo_sgc = m.codigo_sgc AND ie.status = 'Pendente'
    """, conn)

    if membros.empty:
        st.success("🎉 Nenhum desbravador tem débitos pendentes!")
        return

    # Criar coluna formatada "Código SGC - nome"
    membros["display"] = membros["codigo_sgc"] + " - " + membros["nome"]

    # Selecionar membro
    membro_selecionado = st.selectbox("Selecione um Desbravador", membros["display"])

    # Obter o código SGC real do membro selecionado
    codigo_sgc = membros.loc[membros["display"] == membro_selecionado, "codigo_sgc"].values[0]

    # 🔹 Buscar mensalidades pendentes
    mensalidades = pd.read_sql("""
        SELECT um.id_mensalidade, um.status, m.valor, m.mes, m.ano 
        FROM user_mensalidades um
        JOIN mensalidades m ON um.id_mensalidade = m.id
        WHERE um.codigo_sgc = %s AND um.status = 'Pendente'
    """, conn, params=[codigo_sgc])

    # 🔹 Buscar eventos inscritos e não pagos
    eventos = pd.read_sql("""
        SELECT e.nome, e.valor 
        FROM inscricao_eventos ie
        JOIN evento e ON ie.id_evento = e.id
        WHERE ie.codigo_sgc = %s AND ie.status = 'Pendente'
    """, conn, params=[codigo_sgc])

    # Calcular valores totais
    total_mensalidades = mensalidades["valor"].sum() if not mensalidades.empty else 0
    total_eventos = eventos["valor"].sum() if not eventos.empty else 0
    total_debitos = total_mensalidades + total_eventos

    # Exibir os dados
    st.write(f"**📌 Mensalidades Pendentes: {len(mensalidades)}**")
    if not mensalidades.empty:
        st.dataframe(mensalidades[["mes", "ano", "valor"]])

    st.write(f"**📌 Eventos Inscritos e Não Pagos: {len(eventos)}**")
    if not eventos.empty:
        st.dataframe(eventos)

    # Exibir valor total dos débitos
    st.write(f"### 💰 **Total de Débitos: R$ {total_debitos:.2f}**")
    c.close()
    conn.close()


def editar_evento():
    conn, c = conect_db()
    st.subheader("✏️ Gerenciar Evento")

    # Buscar eventos existentes
    eventos = pd.read_sql("SELECT id, nome, valor FROM evento", conn)

    if eventos.empty:
        st.warning("⚠️ Nenhum evento encontrado para gerenciamento.")
        return

    # Selecionar evento para gerenciar
    evento_selecionado = st.selectbox("Selecione o Evento", eventos["nome"], key="select_evento_gerenciar")

    # Obter ID e valor do evento selecionado
    evento_id = eventos.loc[eventos["nome"] == evento_selecionado, "id"].values[0]
    valor_atual = float(eventos.loc[eventos["nome"] == evento_selecionado, "valor"].values[0])

    # Campos de edição
    novo_nome = st.text_input("Novo nome", evento_selecionado)
    novo_valor = st.number_input("Novo Valor", min_value=0.0, value=valor_atual, format="%.2f")

    col1, col2 = st.columns(2)
    evento_id = int(evento_id)
    # Botão para salvar alterações no evento
    if col1.button("💾 Salvar Alterações", key=f"salvar_evento_{evento_id}"):
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE evento 
            SET nome = %s, valor = %s
            WHERE id = %s
        """, (novo_nome, novo_valor, evento_id))
        conn.commit()
        st.success(f"✅ Evento '{novo_nome}' atualizado com sucesso!")
        st.rerun()

    # Botão para deletar evento
    if col2.button("❌ Excluir Evento", key=f"delete_evento_{evento_id}"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inscricao_eventos WHERE id_evento = %s", (evento_id,))
        conn.commit()
        cursor.execute("DELETE FROM evento WHERE id = %s", (evento_id,))
        conn.commit()
        st.warning(f"⚠️ Evento '{evento_selecionado}' e todas as inscrições foram removidos!")
        st.rerun()
    c.close()
    conn.close()


def editar_mensalidade():
    conn, c = conect_db()
    st.subheader("✏️ Editar Mensalidade")

    # Buscar mensalidades existentes
    mensalidades = pd.read_sql("SELECT id, mes, ano, valor FROM mensalidades", conn)

    if mensalidades.empty:
        st.warning("⚠️ Nenhuma mensalidade encontrada para edição.")
        return

    # Criar campo de seleção formatado como "Mês/Ano"
    mensalidades["mes_ano"] = mensalidades["mes"].astype(str) + "/" + mensalidades["ano"].astype(str)
    mensalidade_selecionada = st.selectbox("Selecione a Mensalidade", mensalidades["mes_ano"])

    mensalidade_id = mensalidades.loc[mensalidades["mes_ano"] == mensalidade_selecionada, "id"].values[0]
    valor_atual = mensalidades.loc[mensalidades["mes_ano"] == mensalidade_selecionada, "valor"].values[0]
    st.write(mensalidade_id)
    # Campo de edição do valor
    novo_valor = st.number_input("Novo Valor", min_value=0.0, value=valor_atual, format="%.2f")

    if st.button("💾 Salvar Alterações", key="salvar_mensalidade"):
        cursor = conn.cursor()

        # Atualizar o valor da mensalidade na tabela principal
        cursor.execute("""
            UPDATE mensalidades 
            SET valor = %s
            WHERE id = %s
        """, (novo_valor, mensalidade_id))

        conn.commit()
        st.success(f"✅ Mensalidade '{mensalidade_selecionada}' atualizada com sucesso!")
        st.rerun()
    c.close()
    conn.close()


def gerenciar_caixa():
    conn, c = conect_db()
    st.subheader("📌 Gerenciar Caixa")

    # 🔹 Entrada de dados
    tipo = st.selectbox("Tipo da Transação", ["Entrada", "Saída"])
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.01, format="%.2f")
    data = st.date_input("Data da Transação")

    # 🔹 Buscar eventos disponíveis para vinculação
    eventos = pd.read_sql("SELECT id, nome FROM evento", conn)
    eventos_dict = {f"{row['nome']}": row["id"] for _, row in eventos.iterrows()}
    eventos_dict["Nenhum"] = None  # Opção para não vincular a um evento

    evento_selecionado = st.selectbox("Vincular a um Evento (Opcional)", list(eventos_dict.keys()))
    id_evento = eventos_dict[evento_selecionado]

    if st.button("💾 Registrar Transação"):
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO caixa (tipo, descricao, valor, data, id_evento) 
            VALUES (%s, %s, %s, %s, %s)
        """, (tipo, descricao, valor, data.strftime("%Y-%m-%d"), id_evento))
        conn.commit()
        st.success("✅ Transação registrada com sucesso!")
        st.rerun()

    # 🔹 Exibir registros
    df_caixa = pd.read_sql("""
        SELECT c.id, c.tipo, c.descricao, c.valor, c.data, e.nome as evento_relacionado
        FROM caixa c
        LEFT JOIN evento e ON c.id_evento = e.id
        ORDER BY c.data DESC
    """, conn)

    if not df_caixa.empty:
        st.subheader("📊 Transações Registradas")
        df_caixa.fillna("-", inplace=True)  # Substituir valores nulos por "-"
        st.dataframe(df_caixa)
    else:
        st.info("📌 Nenhuma transação encontrada.")
    c.close()
    conn.close()


def fechamento_mensal():
    conn, c = conect_db()
    st.subheader("📌 Fechamento Mensal")

    # Selecionar o mês e ano
    mes = st.selectbox("Mês", list(range(1, 13)), index=0, format_func=lambda x: f"{x:02d}")
    ano = st.number_input("Ano", min_value=2000, max_value=2100, value=pd.Timestamp.today().year, step=1)

    # Verificar se já foi fechado
    verifica_fechamento = pd.read_sql("SELECT * FROM fechamento WHERE mes = %s AND ano = %s", conn, params=[mes, ano])
    if not verifica_fechamento.empty:
        st.warning("⚠️ Este mês já foi fechado!")
        return

    # Calcular entradas e saídas do mês
    try:
        df_movimentacoes = pd.read_sql("""
            SELECT tipo, SUM(valor) as total 
            FROM caixa 
            WHERE strftime('%m', data) = %s AND strftime('%Y', data) = %s
            GROUP BY tipo
        """, conn, params=[f"{mes:02d}", str(ano)])

        entrada_total = df_movimentacoes[df_movimentacoes["tipo"] == "Entrada"]["total"].sum() if "Entrada" in \
                                                                                                  df_movimentacoes[
                                                                                                      "tipo"].values else 0
        saida_total = df_movimentacoes[df_movimentacoes["tipo"] == "Saída"]["total"].sum() if "Saída" in \
                                                                                              df_movimentacoes[
                                                                                                  "tipo"].values else 0

        st.write(f"**📥 Total de Entradas:** R$ {entrada_total:.2f}")
        st.write(f"**📤 Total de Saídas:** R$ {saida_total:.2f}")

        if st.button("📌 Confirmar Fechamento"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO fechamento (entrada, saida, ano, mes) VALUES (%s, %s, %s, %s)",
                           (entrada_total, saida_total, ano, mes))
            conn.commit()
            st.success("✅ Fechamento do mês registrado com sucesso!")
            st.rerun()

    except Exception as e:
        print(f"Erro ao executar consulta: {e}")


    c.close()
    conn.close()



