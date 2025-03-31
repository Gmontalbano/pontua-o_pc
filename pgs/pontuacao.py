import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from pgs.db import engine, tables


def show_pontos():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    chamadas = tables.get("chamadas")
    reunioes = tables.get("reunioes")
    unidades = tables.get("unidades")

    if chamadas is None or reunioes is None or unidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    with Session(engine) as session:
        chamadas_query = session.execute(
            select(
                chamadas.c.id,
                chamadas.c.reuniao_id,
                reunioes.c.nome.label("Reuniao_Nome"),
                reunioes.c.data.label("Data"),
                unidades.c.nome.label("Unidade_Nome"),
                chamadas.c.id_unidade,
                chamadas.c.presenca,
                chamadas.c.pontualidade,
                chamadas.c.uniforme,
                chamadas.c.modestia
            ).join(reunioes, chamadas.c.reuniao_id == reunioes.c.id)
             .join(unidades, chamadas.c.id_unidade == unidades.c.id)
        ).fetchall()

        df = pd.DataFrame(chamadas_query, columns=[
            "ID", "Reuniao_ID", "Reuniao_Nome", "Data", "Unidade_Nome", "ID_Unidade",
            "Presenca", "Pontualidade", "Uniforme", "Modestia"
        ])

    if df.empty:
        st.info("ℹ️ Nenhuma chamada registrada ainda.")
        return

    # Convertendo a coluna de data
    df["Data"] = pd.to_datetime(df["Data"])
    df["Ano"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month

    # Criar ranking geral
    ranking = df.groupby("Unidade_Nome")[["Presenca", "Pontualidade", "Uniforme", "Modestia"]].sum()
    ranking["Total_Geral"] = ranking.sum(axis=1)
    ranking = ranking.sort_values(by="Total_Geral", ascending=False)

    st.subheader("📌 Ranking Geral das Unidades")

    # 📊 Exibir Top 3 no formato de métricas
    top_3 = ranking.head(3).reset_index()
    col1, col2, col3 = st.columns(3)

    if len(top_3) > 0:
        col1.metric(label=f"🥇 {top_3.iloc[0, 0]}", value=top_3.iloc[0, -1])
    if len(top_3) > 1:
        col2.metric(label=f"🥈 {top_3.iloc[1, 0]}", value=top_3.iloc[1, -1])
    if len(top_3) > 2:
        col3.metric(label=f"🥉 {top_3.iloc[2, 0]}", value=top_3.iloc[2, -1])

    for unidade in df["Unidade_Nome"].unique():
        df_unidade = df[df["Unidade_Nome"] == unidade]
        total_presenca_unidade = df_unidade["Presenca"].sum()
        total_pontualidade_unidade = df_unidade["Pontualidade"].sum()
        total_uniforme_unidade = df_unidade["Uniforme"].sum()
        total_modestia_unidade = df_unidade["Modestia"].sum()
        total_geral_unidade = total_presenca_unidade + total_pontualidade_unidade + total_uniforme_unidade + total_modestia_unidade

        st.subheader(f"📍 Unidade: {unidade}")

        # Resumo geral da unidade
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("✅ Presença", total_presenca_unidade)
        col2.metric("⏰ Pontualidade", total_pontualidade_unidade)
        col3.metric("👔 Uniforme", total_uniforme_unidade)
        col4.metric("🧥 Modéstia", total_modestia_unidade)
        col5.metric("🏆 Total", total_geral_unidade)

        # Detalhamento por mês
        for mes in sorted(df_unidade["Mes"].unique(), reverse=True):  # Ordenado do mais recente para o mais antigo
            df_mes = df_unidade[df_unidade["Mes"] == mes]
            total_presenca = df_mes["Presenca"].sum()
            total_pontualidade = df_mes["Pontualidade"].sum()
            total_uniforme = df_mes["Uniforme"].sum()
            total_modestia = df_mes["Modestia"].sum()
            total_geral = total_presenca + total_pontualidade + total_uniforme + total_modestia

            with st.expander(f"📆 Mês {mes}"):
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("✅ Presença", total_presenca)
                col2.metric("⏰ Pontualidade", total_pontualidade)
                col3.metric("👔 Uniforme", total_uniforme)
                col4.metric("🧥 Modéstia", total_modestia)
                col5.metric("🏆 Total", total_geral)
