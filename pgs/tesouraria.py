import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, update, func, delete
from pgs.db import get_db, engine, tables


def criar_mensalidades():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    mensalidades = tables.get("mensalidades")
    membros = tables.get("membros")
    user_mensalidades = tables.get("user_mensalidades")

    if mensalidades is None or membros is None or user_mensalidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Criar Mensalidades")

    # Entrada de dados para a mensalidade
    ano = st.number_input("Ano", min_value=2024, max_value=2100, value=datetime.now().year, step=1)
    valor = st.number_input("Valor da Mensalidade", min_value=0.0, format="%.2f")

    if st.button("💾 Criar Mensalidades do Ano"):
        with Session(engine) as session:
            # Criar mensalidades para os 12 meses do ano selecionado
            for mes in range(1, 13):
                result = session.execute(
                    insert(mensalidades)
                    .values(valor=valor, ano=ano, mes=mes)
                    .returning(mensalidades.c.id)
                )
                id_mensalidade = result.scalar()

                # Buscar todos os membros com cargo "Desbravador(a)"
                membros_query = session.execute(
                    select(membros.c.codigo_sgc).where(membros.c.cargo == "Desbravador(a)")
                ).fetchall()

                # Criar mensalidade para cada membro
                session.execute(
                    insert(user_mensalidades),
                    [{"id_mensalidade": id_mensalidade, "codigo_sgc": membro[0], "status": "Pendente"} for membro in
                     membros_query]
                )

            session.commit()

        st.success("✅ Mensalidades criadas para os 12 meses e atribuídas aos desbravadores!")


def criar_eventos():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    evento = tables.get("evento")

    if evento is None:
        st.error("❌ A tabela 'evento' não foi encontrada no banco de dados.")
        return

    st.subheader("📌 Criar Eventos")

    nome_evento = st.text_input("Nome do Evento")
    valor_evento = st.number_input("Valor do evento", min_value=0.0, format="%.2f")

    if st.button("💾 Criar Evento"):
        with Session(engine) as session:
            session.execute(
                insert(evento).values(nome=nome_evento, valor=valor_evento)
            )
            session.commit()

        st.success(f"✅ Evento '{nome_evento}' criado com sucesso!")


def inscrever_no_evento():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    evento = tables.get("evento")
    membros = tables.get("membros")
    inscricao_eventos = tables.get("inscricao_eventos")

    if evento is None or membros is None or inscricao_eventos is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Inscrever em Evento")

    # Buscar eventos disponíveis
    with Session(engine) as session:
        eventos_query = session.execute(evento.select()).fetchall()
        membros_query = session.execute(
            select(membros.c.codigo_sgc, membros.c.nome)  # ✅ Seleciona apenas as colunas necessárias
        ).fetchall()

    eventos_df = pd.DataFrame(eventos_query, columns=["id", "valor", "nome"])
    membros_df = pd.DataFrame(membros_query, columns=["codigo_sgc", "nome"])

    if eventos_df.empty:
        st.warning("⚠️ Nenhum evento encontrado. Cadastre um evento antes de inscrever participantes.")
        return

    if membros_df.empty:
        st.warning("⚠️ Nenhum desbravador encontrado para inscrição.")
        return

    # Selecionar evento
    evento_selecionado = st.selectbox("Selecione um Evento", eventos_df["nome"], key="select_evento")
    evento_id = eventos_df.loc[eventos_df["nome"] == evento_selecionado, "id"].values[0]

    # Criar coluna formatada para exibir "Código SGC - Nome"
    membros_df["display"] = membros_df["codigo_sgc"].astype(str) + " - " + membros_df["nome"]

    # Selecionar o membro no formato desejado
    membro_selecionado = st.selectbox("Selecione um Desbravador", membros_df["display"], key="select_membro")

    # Obter o código SGC real a partir da seleção
    codigo_sgc = str(membros_df.loc[membros_df["display"] == membro_selecionado, "codigo_sgc"].values[0])
    if st.button("💾 Inscrever"):
        with Session(engine) as session:
            session.execute(
                insert(inscricao_eventos).values(
                    codigo_sgc=codigo_sgc,
                    id_evento=int(evento_id),
                    status="Pendente"
                )
            )
            session.commit()

        st.success(f"✅ {membro_selecionado} foi inscrito no evento '{evento_selecionado}'!")
        st.rerun()


def editar_status_inscricao():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    evento = tables.get("evento")
    membros = tables.get("membros")
    inscricao_eventos = tables.get("inscricao_eventos")
    caixa = tables.get("caixa")

    if evento is None or membros is None or inscricao_eventos is None or caixa is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("✏️ Editar Status de Pagamento")

    # Buscar eventos existentes
    with Session(engine) as session:
        eventos_query = session.execute(evento.select()).fetchall()

    eventos_df = pd.DataFrame(eventos_query, columns=["id", "valor", "nome"])

    if eventos_df.empty:
        st.warning("⚠️ Nenhum evento encontrado.")
        return

    # Selecionar um evento
    evento_selecionado = st.selectbox(
        "Selecione um Evento",
        eventos_df["nome"],
        key="editar_evento"
    )

    # Obter ID e valor do evento selecionado
    evento_id = int(eventos_df.loc[eventos_df["nome"] == evento_selecionado, "id"].values[0])
    valor_evento = float(eventos_df.loc[eventos_df["id"] == evento_id, "valor"].values[0])
    st.write(f"💰 **Valor do Evento:** R$ {valor_evento:.2f}")

    # Buscar inscritos no evento
    with Session(engine) as session:
        inscritos_query = session.execute(
            select(
                inscricao_eventos.c.codigo_sgc,  # ✅ Seleciona apenas `codigo_sgc`
                membros.c.nome,  # ✅ Pega `nome` da tabela `membros`
                inscricao_eventos.c.status  # ✅ Seleciona `status`
            )
            .join(membros, membros.c.codigo_sgc == inscricao_eventos.c.codigo_sgc)  # ✅ Faz o JOIN corretamente
            .where(inscricao_eventos.c.id_evento == evento_id)  # ✅ Filtra pelo evento desejado
        ).fetchall()

    # Criar DataFrame apenas com as colunas necessárias
    inscritos_df = pd.DataFrame(inscritos_query, columns=["codigo_sgc", "nome", "status"])

    if inscritos_df.empty:
        st.info("📌 Nenhum desbravador está inscrito neste evento.")
        return

    # Criar coluna "Código SGC - Nome" para exibição
    inscritos_df["display"] = inscritos_df["codigo_sgc"] + " - " + inscritos_df["nome"]

    # Selecionar um inscrito para edição
    inscrito_selecionado = st.selectbox("Selecione um Desbravador", inscritos_df["display"], key=f"inscrito_{evento_id}")

    # Obter o código SGC do inscrito selecionado
    codigo_sgc = inscritos_df.loc[inscritos_df["display"] == inscrito_selecionado, "codigo_sgc"].values[0]

    # Obter status atual do inscrito
    status_atual = inscritos_df.loc[inscritos_df["display"] == inscrito_selecionado, "status"].values[0]

    # Criar selectbox para editar status
    novo_status = st.selectbox(
        "Status:",
        ["Pendente", "Pago", "Cancelado"],
        index=["Pendente", "Pago", "Cancelado"].index(status_atual),
        key=f"status_{codigo_sgc}_{evento_id}"
    )

    # Botão para atualizar status
    if st.button("💾 Atualizar Status", key=f"atualizar_status_evento_{evento_id}"):
        with Session(engine) as session:
            # Apenas atualizar se houve mudança no status
            if status_atual != novo_status:
                session.execute(
                    update(inscricao_eventos)
                    .where(
                        (inscricao_eventos.c.id_evento == evento_id) &
                        (inscricao_eventos.c.codigo_sgc == codigo_sgc)
                    )
                    .values(status=novo_status)
                )

                # Se mudou de "Pendente" ou "Cancelado" para "Pago", registrar no caixa
                if novo_status == "Pago" and status_atual != "Pago":
                    descricao = f"Evento {evento_selecionado} - {codigo_sgc}"
                    data_hoje = pd.Timestamp.today().strftime("%Y-%m-%d")

                    session.execute(
                        insert(caixa).values(
                            tipo="Entrada",
                            descricao=descricao,
                            valor=valor_evento,
                            data=data_hoje,
                            id_evento=evento_id
                        )
                    )

                session.commit()

        st.success(f"✅ Status atualizado com sucesso para {inscrito_selecionado}!")
        st.rerun()


def remover_inscricao():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    evento = tables.get("evento")
    membros = tables.get("membros")
    inscricao_eventos = tables.get("inscricao_eventos")

    if evento is None or membros is None or inscricao_eventos is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("🗑️ Remover Inscrição")

    # Buscar eventos disponíveis
    with Session(engine) as session:
        eventos_query = session.execute(select(evento.c.id, evento.c.nome)).fetchall()

    eventos_df = pd.DataFrame(eventos_query, columns=["id", "nome"])

    if eventos_df.empty:
        st.warning("⚠️ Nenhum evento encontrado.")
        return

    # Selecionar evento
    evento_selecionado = st.selectbox("Selecione um Evento", eventos_df["nome"], key="remover_evento")
    evento_id = str(eventos_df.loc[eventos_df["nome"] == evento_selecionado, "id"].values[0])

    # Buscar inscritos no evento
    with Session(engine) as session:
        inscritos_query = session.execute(
            select(inscricao_eventos.c.codigo_sgc, membros.c.nome)  # Correção aqui
            .join(membros, membros.c.codigo_sgc == inscricao_eventos.c.codigo_sgc)
            .where(inscricao_eventos.c.id_evento == evento_id)
        ).fetchall()

    inscritos_df = pd.DataFrame(inscritos_query, columns=["codigo_sgc", "nome"])

    if inscritos_df.empty:
        st.info("📌 Nenhum desbravador está inscrito neste evento.")
        return

    # Selecionar inscrito para remover
    inscrito_selecionado = st.selectbox("Selecione um Desbravador para remover", inscritos_df["nome"], key="select_remover")
    codigo_sgc = inscritos_df.loc[inscritos_df["nome"] == inscrito_selecionado, "codigo_sgc"].values[0]

    if st.button("❌ Remover Inscrição", key="remover_inscricao"):
        with Session(engine) as session:
            session.execute(
                delete(inscricao_eventos)
                .where(
                    (inscricao_eventos.c.id_evento == evento_id) &
                    (inscricao_eventos.c.codigo_sgc == codigo_sgc)
                )
            )
            session.commit()

        st.warning(f"⚠️ {inscrito_selecionado} foi removido do evento '{evento_selecionado}'.")
        st.rerun()


def visualizar_relatorios():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    fechamento = tables.get("fechamento")
    caixa = tables.get("caixa")
    evento = tables.get("evento")
    user_mensalidades = tables.get("user_mensalidades")
    mensalidades = tables.get("mensalidades")

    if fechamento is None or caixa is None or evento is None or user_mensalidades is None or mensalidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📊 Relatórios Financeiros")

    # 🔹 Visão Geral por Ano
    with Session(engine) as session:
        df_ano = pd.DataFrame(
            session.execute(
                select(
                    fechamento.c.ano,
                    func.sum(fechamento.c.entrada).label("total_entradas"),
                    func.sum(fechamento.c.saida).label("total_saidas")
                )
                .group_by(fechamento.c.ano)
                .order_by(fechamento.c.ano.desc())
            ).fetchall(),
            columns=["Ano", "Total Entradas", "Total Saídas"]
        )

    st.subheader("📆 Visão Geral por Ano")
    if df_ano.empty:
        st.info("📌 Nenhum dado encontrado.")
    else:
        st.dataframe(df_ano)

    # 🔹 Visão Geral por Mês
    with Session(engine) as session:
        df_mes = pd.DataFrame(
            session.execute(
                select(
                    fechamento.c.ano,
                    fechamento.c.mes,
                    fechamento.c.entrada.label("total_entradas"),
                    fechamento.c.saida.label("total_saidas")
                )
                .order_by(fechamento.c.ano.desc(), fechamento.c.mes.desc())
            ).fetchall(),
            columns=["Ano", "Mês", "Total Entradas", "Total Saídas"]
        )

    if not df_mes.empty:
        df_mes["Mês/Ano"] = df_mes["Mês"].astype(str) + "/" + df_mes["Ano"].astype(str)
        df_mes = df_mes[["Mês/Ano", "Total Entradas", "Total Saídas"]]

    st.subheader("📅 Visão Geral por Mês")
    st.dataframe(df_mes if not df_mes.empty else st.info("📌 Nenhum dado encontrado."))

    # 🔹 Relatório por Evento
    st.subheader("🎯 Relatório por Evento")

    with Session(engine) as session:
        eventos_query = session.execute(
            select(evento.c.id, evento.c.nome)
            .distinct()
            .join(caixa, evento.c.id == caixa.c.id_evento)
        ).fetchall()

    eventos_df = pd.DataFrame(eventos_query, columns=["id", "nome"])

    if not eventos_df.empty:
        evento_dict = {row["nome"]: row["id"] for _, row in eventos_df.iterrows()}
        evento_selecionado = st.selectbox("Selecione um Evento", list(evento_dict.keys()))
        evento_id = evento_dict[evento_selecionado]

        with Session(engine) as session:
            df_evento = pd.DataFrame(
                session.execute(
                    select(caixa.c.data, caixa.c.tipo, caixa.c.descricao, caixa.c.valor)
                    .where(caixa.c.id_evento == evento_id)
                    .order_by(caixa.c.data.desc())
                ).fetchall(),
                columns=["Data", "Tipo", "Descrição", "Valor"]
            )

        if not df_evento.empty:
            total_entradas = df_evento[df_evento["Tipo"] == "Entrada"]["Valor"].sum()
            total_saidas = df_evento[df_evento["Tipo"] == "Saída"]["Valor"].sum()
            saldo_evento = total_entradas - total_saidas

            st.write(f"📥 **Total Entradas:** R$ {total_entradas:.2f}")
            st.write(f"📤 **Total Saídas:** R$ {total_saidas:.2f}")
            st.write(f"💰 **Saldo do Evento:** R$ {saldo_evento:.2f}")
            st.dataframe(df_evento)
        else:
            st.info("📌 Nenhuma movimentação registrada para este evento.")

    else:
        st.warning("⚠️ Nenhum evento com movimentação financeira encontrado.")

    # 🔹 Cálculo do Caixa e Custos
    st.subheader("💰 Cálculo do Caixa e Custos")
    with Session(engine) as session:
        df_total = session.execute(
            select(
                func.sum(fechamento.c.entrada).label("total_entradas"),
                func.sum(fechamento.c.saida).label("total_saidas")
            )
        ).fetchone()

    total_entradas = df_total.total_entradas or 0
    total_saidas = df_total.total_saidas or 0
    saldo_final = total_entradas - total_saidas

    st.write(f"📥 **Total de Entradas:** R$ {total_entradas:.2f}")
    st.write(f"📤 **Total de Saídas:** R$ {total_saidas:.2f}")
    st.write(f"💵 **Saldo Final:** R$ {saldo_final:.2f}")

    # 🔹 Indicadores de Mensalidades
    st.subheader("📊 Indicadores de Mensalidades")

    with Session(engine) as session:
        df_mensalidades = pd.DataFrame(
            session.execute(
                select(
                    user_mensalidades.c.status,
                    func.count().label("total_mensalidades"),
                    func.count(user_mensalidades.c.codigo_sgc.distinct()).label("total_usuarios")
                )
                .group_by(user_mensalidades.c.status)
            ).fetchall(),
            columns=["Status", "Total Mensalidades", "Total Usuários"]
        )

    if not df_mensalidades.empty:
        for status in ["Pago", "Pendente", "Isento"]:
            total_mensalidades = df_mensalidades[df_mensalidades["Status"] == status]["Total Mensalidades"].sum()
            total_usuarios = df_mensalidades[df_mensalidades["Status"] == status]["Total Usuários"].sum()
            st.write(f"✅ **{status}:** {total_mensalidades} mensalidades - {total_usuarios} usuários")
    else:
        st.info("📌 Nenhum dado encontrado para mensalidades.")

    # 🔹 Mensalidades Detalhadas por Mês/Ano
    st.subheader("📊 Mensalidades Detalhadas")

    with Session(engine) as session:
        anos_query = session.execute(select(mensalidades.c.ano.distinct()).order_by(mensalidades.c.ano.desc())).fetchall()

    anos_df = pd.DataFrame(anos_query, columns=["Ano"])

    if not anos_df.empty:
        ano_selecionado = st.selectbox("Selecione o Ano", anos_df["Ano"])

        with Session(engine) as session:
            meses_query = session.execute(
                select(mensalidades.c.mes.distinct())
                .where(mensalidades.c.ano == ano_selecionado)
                .order_by(mensalidades.c.mes.asc())
            ).fetchall()

        meses_df = pd.DataFrame(meses_query, columns=["Mês"])

        if not meses_df.empty:
            mes_selecionado = st.selectbox("Selecione o Mês", meses_df["Mês"])
            # Aqui você pode puxar dados detalhados como feito anteriormente
        else:
            st.info("📌 Nenhum dado encontrado para este ano.")

    else:
        st.warning("⚠️ Nenhum dado encontrado na tabela de mensalidades.")


def editar_status_mensalidade():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    user_mensalidades = tables.get("user_mensalidades")
    mensalidades = tables.get("mensalidades")
    caixa = tables.get("caixa")

    if membros is None or user_mensalidades is None or mensalidades is None or caixa is None:
        st.error("❌ Algumas tabelas necessárias não foram encontradas no banco de dados.")
        return

    st.subheader("✏️ Editar Status de Pagamento")

    # Buscar desbravadores com mensalidades
    with Session(engine) as session:
        result = session.execute(
            select(membros.c.codigo_sgc, membros.c.nome)
            .join(user_mensalidades, membros.c.codigo_sgc == user_mensalidades.c.codigo_sgc)
            .where(membros.c.cargo == "Desbravador(a)")
            .distinct()
            .order_by(membros.c.nome)
        ).fetchall()

    if not result:
        st.warning("⚠️ Nenhum desbravador encontrado com mensalidades registradas.")
        return

    # Criar selectbox formatado
    df_desbravadores = pd.DataFrame(result, columns=["codigo_sgc", "nome"])
    desbravador_dict = {f"{row['nome']} ({row['codigo_sgc']})": row["codigo_sgc"] for _, row in
                        df_desbravadores.iterrows()}
    desbravador_selecionado = st.selectbox("Selecione um Desbravador", list(desbravador_dict.keys()))

    codigo_sgc = desbravador_dict[desbravador_selecionado]

    # Buscar mensalidades do desbravador
    with Session(engine) as session:
        result = session.execute(
            select(user_mensalidades.c.id_mensalidade, user_mensalidades.c.status,
                   mensalidades.c.ano, mensalidades.c.mes, mensalidades.c.valor)
            .join(mensalidades, user_mensalidades.c.id_mensalidade == mensalidades.c.id)
            .where(user_mensalidades.c.codigo_sgc == codigo_sgc)
            .order_by(mensalidades.c.ano, mensalidades.c.mes)
        ).fetchall()

    if not result:
        st.info("📌 Este desbravador não tem mensalidades registradas.")
        return

    df_mensalidades = pd.DataFrame(result, columns=["id_mensalidade", "status", "ano", "mes", "valor"])

    novos_status = {}

    for _, row in df_mensalidades.iterrows():
        id_mensalidade, status_atual, ano, mes, valor = row
        novo_status = st.selectbox(
            f"📆 {mes}/{ano} - R$ {valor:.2f}",
            ["Pendente", "Pago", "Isento"],
            index=["Pendente", "Pago", "Isento"].index(status_atual),
            key=f"status_{id_mensalidade}_{codigo_sgc}"
        )
        novos_status[id_mensalidade] = (status_atual, novo_status, valor)

    col1, col2 = st.columns(2)

    # **Salvar Alterações**
    if col1.button("💾 Atualizar Status", key="atualizar_status"):
        with Session(engine) as session:
            try:
                for id_mensalidade, (status_atual, novo_status, valor) in novos_status.items():
                    if status_atual != novo_status:
                        session.execute(
                            update(user_mensalidades)
                            .where(user_mensalidades.c.id_mensalidade == id_mensalidade,
                                   user_mensalidades.c.codigo_sgc == codigo_sgc)
                            .values(status=novo_status)
                        )

                        if novo_status == "Pago" and status_atual != "Pago":
                            session.execute(
                                insert(caixa).values(
                                    tipo="Entrada",
                                    descricao=f"Mensalidade - {codigo_sgc}",
                                    valor=valor,
                                    data=pd.Timestamp.today().strftime("%Y-%m-%d")
                                )
                            )

                session.commit()
                st.success("✅ Status atualizado com sucesso!")
                st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"❌ Erro ao atualizar status: {e}")

    # **Cancelar Edição**
    if col2.button("❌ Cancelar", key="cancelar_edicao"):
        st.warning("⚠️ Edição cancelada.")
        st.rerun()


def visualizar_debitos():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    user_mensalidades = tables.get("user_mensalidades")
    mensalidades = tables.get("mensalidades")
    inscricao_eventos = tables.get("inscricao_eventos")
    eventos = tables.get("evento")

    if not membros or not user_mensalidades or not mensalidades or not inscricao_eventos or not eventos:
        st.error("❌ Algumas tabelas necessárias não foram encontradas no banco de dados.")
        return

    st.subheader("💰 Débitos dos Desbravadores")

    # Buscar desbravadores que possuem mensalidades ou eventos pendentes
    with Session(engine) as session:
        result = session.execute(
            select(membros.c.codigo_sgc, membros.c.nome)
            .outerjoin(user_mensalidades,
                       (user_mensalidades.c.codigo_sgc == membros.c.codigo_sgc) &
                       (user_mensalidades.c.status == "Pendente"))
            .outerjoin(inscricao_eventos,
                       (inscricao_eventos.c.codigo_sgc == membros.c.codigo_sgc) &
                       (inscricao_eventos.c.status == "Pendente"))
            .distinct()
        ).fetchall()

    if not result:
        st.success("🎉 Nenhum desbravador tem débitos pendentes!")
        return

    df_membros = pd.DataFrame(result, columns=["codigo_sgc", "nome"])
    membro_dict = {f"{row['nome']} ({row['codigo_sgc']})": row["codigo_sgc"] for _, row in df_membros.iterrows()}
    membro_selecionado = st.selectbox("Selecione um Desbravador", list(membro_dict.keys()))

    codigo_sgc = membro_dict[membro_selecionado]

    # 🔹 Buscar mensalidades pendentes
    with Session(engine) as session:
        result_mensalidades = session.execute(
            select(user_mensalidades.c.id_mensalidade, user_mensalidades.c.status,
                   mensalidades.c.valor, mensalidades.c.mes, mensalidades.c.ano)
            .join(mensalidades, user_mensalidades.c.id_mensalidade == mensalidades.c.id)
            .where(user_mensalidades.c.codigo_sgc == codigo_sgc, user_mensalidades.c.status == "Pendente")
        ).fetchall()

    df_mensalidades = pd.DataFrame(result_mensalidades, columns=["id_mensalidade", "status", "valor", "mes", "ano"])
    total_mensalidades = df_mensalidades["valor"].sum() if not df_mensalidades.empty else 0

    # 🔹 Buscar eventos inscritos e não pagos
    with Session(engine) as session:
        result_eventos = session.execute(
            select(eventos.c.nome, eventos.c.valor)
            .join(inscricao_eventos, eventos.c.id == inscricao_eventos.c.id_evento)
            .where(inscricao_eventos.c.codigo_sgc == codigo_sgc, inscricao_eventos.c.status == "Pendente")
        ).fetchall()

    df_eventos = pd.DataFrame(result_eventos, columns=["nome", "valor"])
    total_eventos = df_eventos["valor"].sum() if not df_eventos.empty else 0

    total_debitos = total_mensalidades + total_eventos

    # Exibir os dados
    st.write(f"**📌 Mensalidades Pendentes: {len(df_mensalidades)}**")
    if not df_mensalidades.empty:
        st.dataframe(df_mensalidades[["mes", "ano", "valor"]])

    st.write(f"**📌 Eventos Inscritos e Não Pagos: {len(df_eventos)}**")
    if not df_eventos.empty:
        st.dataframe(df_eventos)

    # Exibir valor total dos débitos
    st.write(f"### 💰 **Total de Débitos: R$ {total_debitos:.2f}**")


def editar_evento():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    evento = tables.get("evento")
    inscricao_eventos = tables.get("inscricao_eventos")
    evento_documentos = tables.get("evento_documentos")
    caixa = tables.get("caixa")


    if evento is None or inscricao_eventos is None:
        st.error("❌ As tabelas 'evento' ou 'inscricao_eventos' não foram encontradas no banco de dados.")
        return

    st.subheader("✏️ Gerenciar Evento")

    # Buscar eventos existentes
    with Session(engine) as session:
        result = session.execute(select(evento.c.id, evento.c.nome, evento.c.valor)).fetchall()

    if not result:
        st.warning("⚠️ Nenhum evento encontrado para gerenciamento.")
        return

    df_eventos = pd.DataFrame(result, columns=["id", "nome", "valor"])
    evento_dict = {row["nome"]: row["id"] for _, row in df_eventos.iterrows()}
    evento_selecionado = st.selectbox("Selecione o Evento", list(evento_dict.keys()), key="select_evento_gerenciar")

    evento_id = evento_dict[evento_selecionado]
    evento_info = df_eventos[df_eventos["id"] == evento_id].iloc[0]

    # Campos de edição
    novo_nome = st.text_input("Novo nome", evento_info["nome"])
    novo_valor = st.number_input("Novo Valor", min_value=0.0, value=float(evento_info["valor"]), format="%.2f")

    col1, col2 = st.columns(2)

    # **Salvar Alterações**
    if col1.button("💾 Salvar Alterações", key=f"salvar_evento_{evento_id}"):
        with Session(engine) as session:
            stmt = update(evento).where(evento.c.id == evento_id).values(nome=novo_nome, valor=novo_valor)
            session.execute(stmt)
            session.commit()

        st.success(f"✅ Evento '{novo_nome}' atualizado com sucesso!")
        st.rerun()

    # **Excluir Evento**
    if col2.button("❌ Excluir Evento", key=f"delete_evento_{evento_id}"):
        with Session(engine) as session:
            try:
                # Verifica se há registros na tabela 'caixa' que impedem a exclusão
                caixa_vinculado = session.execute(
                    select(caixa.c.id).where(caixa.c.id_evento == evento_id)
                ).fetchone()

                if caixa_vinculado:
                    st.error("❌ Não é possível excluir este evento porque há registros na tabela 'caixa'.")
                else:
                    # Deleta primeiro as inscrições relacionadas ao evento
                    session.execute(delete(evento_documentos).where(evento_documentos.c.id_evento == evento_id))
                    session.execute(delete(inscricao_eventos).where(inscricao_eventos.c.id_evento == evento_id))
                    session.execute(delete(evento).where(evento.c.id == evento_id))
                    session.commit()
                    st.warning(f"⚠️ Evento '{evento_selecionado}' e todas as inscrições foram removidos!")
                    st.rerun()
            except Exception as e:
                session.rollback()
                st.error(f"❌ Erro ao excluir o evento: {str(e)}")




def editar_mensalidade():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    mensalidades = tables.get("mensalidades")

    if mensalidades is None:
        st.error("❌ A tabela 'mensalidades' não foi encontrada no banco de dados.")
        return

    st.subheader("✏️ Editar Mensalidade")

    # Buscar mensalidades existentes
    with Session(engine) as session:
        result = session.execute(select(mensalidades.c.id, mensalidades.c.mes, mensalidades.c.ano, mensalidades.c.valor)).fetchall()

    if not result:
        st.warning("⚠️ Nenhuma mensalidade encontrada para edição.")
        return

    df_mensalidades = pd.DataFrame(result, columns=["id", "mes", "ano", "valor"])
    df_mensalidades["mes_ano"] = df_mensalidades["mes"].astype(str) + "/" + df_mensalidades["ano"].astype(str)

    mensalidade_dict = {row["mes_ano"]: row["id"] for _, row in df_mensalidades.iterrows()}
    mensalidade_selecionada = st.selectbox("Selecione a Mensalidade", list(mensalidade_dict.keys()))

    mensalidade_id = mensalidade_dict[mensalidade_selecionada]
    mensalidade_info = df_mensalidades[df_mensalidades["id"] == mensalidade_id].iloc[0]

    # Campo de edição do valor
    novo_valor = st.number_input("Novo Valor", min_value=0.0, value=float(mensalidade_info["valor"]), format="%.2f")

    if st.button("💾 Salvar Alterações", key="salvar_mensalidade"):
        with Session(engine) as session:
            stmt = update(mensalidades).where(mensalidades.c.id == mensalidade_id).values(valor=novo_valor)
            session.execute(stmt)
            session.commit()

        st.success(f"✅ Mensalidade '{mensalidade_selecionada}' atualizada com sucesso!")
        st.rerun()


def gerenciar_caixa():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    caixa = tables.get("caixa")
    evento = tables.get("evento")

    if caixa is None:
        st.error("❌ A tabela 'caixa' não foi encontrada no banco de dados.")
        return

    st.subheader("📌 Gerenciar Caixa")

    # 🔹 Entrada de dados
    tipo = st.selectbox("Tipo da Transação", ["Entrada", "Saída"])
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.01, format="%.2f")
    data = st.date_input("Data da Transação")

    # 🔹 Buscar eventos disponíveis para vinculação
    with Session(engine) as session:
        result = session.execute(select(evento.c.id, evento.c.nome)).mappings().all()

    eventos_dict = {row["nome"]: row["id"] for row in result}
    eventos_dict["Nenhum"] = None  # Opção para não vincular a um evento
    evento_selecionado = st.selectbox("Vincular a um Evento (Opcional)", list(eventos_dict.keys()))
    id_evento = eventos_dict[evento_selecionado]

    # 🔹 Registrar transação
    if st.button("💾 Registrar Transação"):
        with Session(engine) as session:
            stmt = insert(caixa).values(
                tipo=tipo,
                descricao=descricao,
                valor=valor,
                data=data.strftime("%Y-%m-%d"),
                id_evento=id_evento
            )
            session.execute(stmt)
            session.commit()

        st.success("✅ Transação registrada com sucesso!")
        st.rerun()

    # 🔹 Exibir registros
    with Session(engine) as session:
        result = session.execute(
            select(caixa.c.id, caixa.c.tipo, caixa.c.descricao, caixa.c.valor, caixa.c.data, evento.c.nome.label("evento_relacionado"))
            .outerjoin(evento, caixa.c.id_evento == evento.c.id)
            .order_by(caixa.c.data.desc())
        ).fetchall()

    if result:
        st.subheader("📊 Transações Registradas")
        df_caixa = pd.DataFrame(result, columns=["ID", "Tipo", "Descrição", "Valor", "Data", "Evento Relacionado"])
        df_caixa.fillna("-", inplace=True)  # Substituir valores nulos por "-"
        st.dataframe(df_caixa)
    else:
        st.info("📌 Nenhuma transação encontrada.")


def fechamento_mensal():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    caixa = tables.get("caixa")
    fechamento = tables.get("fechamento")

    if caixa is None or fechamento is None:
        st.error("❌ As tabelas 'caixa' ou 'fechamento' não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Fechamento Mensal")

    # 🔹 Selecionar o mês e ano
    mes = st.selectbox("Mês", list(range(1, 13)), index=0, format_func=lambda x: f"{x:02d}")
    ano = st.number_input("Ano", min_value=2000, max_value=2100, value=pd.Timestamp.today().year, step=1)

    # 🔹 Verificar se já foi fechado
    with Session(engine) as session:
        fechado = session.execute(
            select(fechamento).where(fechamento.c.mes == mes, fechamento.c.ano == ano)
        ).fetchone()

    if fechado:
        st.warning("⚠️ Este mês já foi fechado!")
        return

    # 🔹 Calcular entradas e saídas do mês
    with Session(engine) as session:
        query = session.execute(
            select(caixa.c.tipo, func.sum(caixa.c.valor).label("total"))
            .where(func.to_char(caixa.c.data, 'MM') == f"{mes:02d}")  # Mês com dois dígitos
            .where(func.to_char(caixa.c.data, 'YYYY') == str(ano))  # Ano como string
            .group_by(caixa.c.tipo)
        ).fetchall()

    df_movimentacoes = pd.DataFrame(query, columns=["tipo", "total"])
    entrada_total = df_movimentacoes.loc[df_movimentacoes["tipo"] == "Entrada", "total"].sum() if "Entrada" in df_movimentacoes["tipo"].values else 0
    saida_total = df_movimentacoes.loc[df_movimentacoes["tipo"] == "Saída", "total"].sum() if "Saída" in df_movimentacoes["tipo"].values else 0

    st.write(f"**📥 Total de Entradas:** R$ {entrada_total:.2f}")
    st.write(f"**📤 Total de Saídas:** R$ {saida_total:.2f}")

    # 🔹 Confirmar fechamento do mês
    if st.button("📌 Confirmar Fechamento"):
        with Session(engine) as session:
            stmt = insert(fechamento).values(entrada=entrada_total, saida=saida_total, ano=ano, mes=mes)
            session.execute(stmt)
            session.commit()

        st.success("✅ Fechamento do mês registrado com sucesso!")
        st.rerun()