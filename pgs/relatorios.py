import streamlit as st
import pandas as pd


def show_relatorios(conn):
    st.subheader("Relatórios por Unidade")

    # Carregar dados corretamente
    chamadas = pd.read_sql("""
        SELECT 
    chamadas.*, 
    reunioes.Nome AS Reuniao_Nome, 
    reunioes.Data AS Data,  -- Pegando a data da reunião
    unidades.Nome AS Unidade_Nome
    FROM chamadas
    JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID
    JOIN unidades ON chamadas.id_unidade = unidades.ID
    """, conn)

    chamadas['Data'] = pd.to_datetime(chamadas['Data'])
    chamadas['Mês'] = chamadas['Data'].dt.strftime('%Y-%m')
    chamadas['Ano'] = chamadas['Data'].dt.year

    # Criar ranking geral
    ranking = chamadas.groupby('Unidade_Nome')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum()
    ranking['Total Geral'] = ranking.sum(axis=1)
    ranking = ranking.sort_values(by='Total Geral', ascending=False)

    # Exibir ranking
    st.subheader("Ranking Geral das Unidades")
    st.dataframe(ranking)

    # Exibir relatórios por unidade
    for unidade in chamadas['Unidade_Nome'].unique():
        st.subheader(f"Unidade: {unidade}")
        df_unidade = chamadas[chamadas['Unidade_Nome'] == unidade]

        df_resumo = df_unidade.groupby('Mês')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum().reset_index()
        df_resumo['Total Geral'] = df_resumo[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum(axis=1)

        st.dataframe(df_resumo)
