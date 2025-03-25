import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from pgs.db import get_db, engine, tables


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

    df["Data"] = pd.to_datetime(df["Data"])
    df["Ano"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month

    # Criar ranking geral
    ranking = df.groupby("Unidade_Nome")[["Presenca", "Pontualidade", "Uniforme", "Modestia"]].sum()
    ranking["Total_Geral"] = ranking.sum(axis=1)
    ranking = ranking.sort_values(by="Total_Geral", ascending=False)

    st.subheader("📌 Ranking Geral das Unidades")
    st.dataframe(ranking)

    # Exibir relatórios por unidade
    for unidade in df["Unidade_Nome"].unique():
        st.subheader(f"📍 Unidade: {unidade}")
        df_unidade = df[df["Unidade_Nome"] == unidade]

        df_resumo = df_unidade.groupby("Mes")[["Presenca", "Pontualidade", "Uniforme", "Modestia"]].sum().reset_index()
        df_resumo["Total_Geral"] = df_resumo[["Presenca", "Pontualidade", "Uniforme", "Modestia"]].sum(axis=1)

        st.dataframe(df_resumo)
