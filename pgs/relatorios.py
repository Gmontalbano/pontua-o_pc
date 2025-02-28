import streamlit as st
import pandas as pd


def show_relatorios(conn):
    st.subheader("Relatórios por Unidade")

    # Carregar dados
    chamadas = pd.read_sql("SELECT * FROM chamadas JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID", conn)
    chamadas['Data'] = pd.to_datetime(chamadas['Data'])
    chamadas['Mês'] = chamadas['Data'].dt.strftime('%Y-%m')
    chamadas['Ano'] = chamadas['Data'].dt.year

    # Opções de período
    opcao_periodo = st.radio("Selecione o período:", ["Reunião", "Mensal", "Anual"])

    # Criar ranking geral
    ranking = chamadas.groupby('Unidade')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum()
    ranking['Total Geral'] = ranking.sum(axis=1)
    ranking = ranking.sort_values(by='Total Geral', ascending=False)

    # Exibir ranking
    st.subheader("Ranking Geral das Unidades")
    st.dataframe(ranking)

    # Exibir relatórios por unidade
    unidades = chamadas['Unidade'].unique()
    for unidade in unidades:
        st.subheader(f"Unidade: {unidade}")
        df_unidade = chamadas[chamadas['Unidade'] == unidade]

        # Filtrar por período
        if opcao_periodo == "Reunião":
            df_resumo = df_unidade.groupby('Data')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum().reset_index()
            eixo_x = "Data"
        elif opcao_periodo == "Mensal":
            df_resumo = df_unidade.groupby('Mês')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum().reset_index()
            eixo_x = "Mês"
        else:  # Anual
            df_resumo = df_unidade.groupby('Ano')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum().reset_index()
            eixo_x = "Ano"

        df_resumo['Total Geral'] = df_resumo[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum(axis=1)

        # Exibir tabela
        st.dataframe(df_resumo)