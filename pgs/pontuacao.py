import streamlit as st
import pandas as pd

from pgs.db import conect_db


def show_pontos():
    conn, c = conect_db()
    st.subheader("Pontuação por Unidade")

    # Carregar dados corretamente
    chamadas = pd.read_sql("""
        SELECT 
            chamadas.*, 
            reunioes.nome AS Reuniao_Nome, 
            reunioes.data::DATE AS Data, 
            unidades.nome AS Unidade_Nome,
            EXTRACT(YEAR FROM reunioes.data) AS Ano, 
            EXTRACT(MONTH FROM reunioes.data) AS Mês
        FROM chamadas
        JOIN reunioes ON chamadas.reuniao_id = reunioes.id
        JOIN unidades ON chamadas.id_unidade = unidades.id
    """, conn)

    # Criar ranking geral
    ranking = chamadas.groupby('unidade_nome')[['presenca', 'pontualidade', 'uniforme', 'modestia']].sum()
    ranking['Total Geral'] = ranking.sum(axis=1)
    ranking = ranking.sort_values(by='Total Geral', ascending=False)

    # Exibir ranking
    st.subheader("Ranking Geral das Unidades")
    st.dataframe(ranking)

    # Exibir relatórios por unidade
    for unidade in chamadas['unidade_nome'].unique():
        st.subheader(f"Unidade: {unidade}")
        df_unidade = chamadas[chamadas['unidade_nome'] == unidade]

        df_resumo = df_unidade.groupby('mês')[['presenca', 'pontualidade', 'uniforme', 'modestia']].sum().reset_index()
        df_resumo['Total Geral'] = df_resumo[['presenca', 'pontualidade', 'uniforme', 'modestia']].sum(axis=1)

        st.dataframe(df_resumo)
    c.close()
    conn.close()
