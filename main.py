import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Conectar ao banco de dados SQLite
conn = sqlite3.connect('registro_chamada.db')
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS reunioes (ID INTEGER PRIMARY KEY, Nome TEXT, Data TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS unidades (ID INTEGER PRIMARY KEY, Nome TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS membros (ID INTEGER PRIMARY KEY, Nome TEXT, Unidade TEXT)''')
c.execute(
    '''CREATE TABLE IF NOT EXISTS chamadas (Reuniao_ID INTEGER, Unidade TEXT, Membro TEXT, Presenca INTEGER, Pontualidade INTEGER, Uniforme INTEGER, Modestia INTEGER)''')
conn.commit()

st.title("Registro de Chamada")

menu = st.sidebar.radio("Menu",
                        ["Cadastro de Reunião", "Cadastro de Unidade", "Cadastro de Membro", "Registrar Chamada",
                         "Visualizar Chamadas", "Relatórios"])

if menu == "Cadastro de Reunião":
    st.subheader("Cadastro de Reunião")
    nome = st.text_input("Nome da Reunião")
    data = st.date_input("Data", value=datetime.today())
    if st.button("Cadastrar Reunião"):
        c.execute("INSERT INTO reunioes (Nome, Data) VALUES (?, ?)", (nome, data))
        conn.commit()
        st.success("Reunião cadastrada com sucesso!")

elif menu == "Cadastro de Unidade":
    st.subheader("Cadastro de Unidade")
    nome = st.text_input("Nome da Unidade")
    if st.button("Cadastrar Unidade"):
        c.execute("INSERT INTO unidades (Nome) VALUES (?)", (nome,))
        conn.commit()
        st.success("Unidade cadastrada com sucesso!")

elif menu == "Cadastro de Membro":
    st.subheader("Cadastro de Membro")
    unidades = pd.read_sql("SELECT Nome FROM unidades", conn)
    nome = st.text_input("Nome do Membro")
    unidade = st.selectbox("Unidade", unidades['Nome'] if not unidades.empty else [])
    if st.button("Cadastrar Membro"):
        c.execute("INSERT INTO membros (Nome, Unidade) VALUES (?, ?)", (nome, unidade))
        conn.commit()
        st.success("Membro cadastrado com sucesso!")

elif menu == "Registrar Chamada":
    st.subheader("Registrar Chamada")
    reunioes = pd.read_sql("SELECT * FROM reunioes", conn)
    unidades = pd.read_sql("SELECT Nome FROM unidades", conn)

    reuniao = st.selectbox("Reunião", reunioes['Nome'] if not reunioes.empty else [])
    unidade = st.selectbox("Unidade", unidades['Nome'] if not unidades.empty else [])

    if reuniao and unidade:
        membros_unidade = pd.read_sql(f"SELECT Nome FROM membros WHERE Unidade = '{unidade}'", conn)
        registros = []

        for _, row in membros_unidade.iterrows():
            st.subheader(row['Nome'])
            presenca = st.slider("Presença", 0, 10, 5, 1, key=f"presenca_{row['Nome']}")
            pontualidade = st.slider("Pontualidade", 0, 10, 5, 1, key=f"pontualidade_{row['Nome']}")
            uniforme = st.slider("Uniforme", 0, 10, 5, 1, key=f"uniforme_{row['Nome']}")
            modestia = st.slider("Modéstia", 0, 10, 5, 1, key=f"modestia_{row['Nome']}")
            print(reunioes[reunioes['Nome'] == reuniao]['ID'].values[0])
            registros.append((int(reunioes[reunioes['Nome'] == reuniao]['ID'].values[0]),
                              unidade,
                              row['Nome'],
                              presenca,
                              pontualidade,
                              uniforme,
                              modestia))

        if st.button("Salvar Chamada"):
            print(registros)
            c.executemany(
                "INSERT INTO chamadas (Reuniao_ID, Unidade, Membro, Presenca, Pontualidade, Uniforme, Modestia) VALUES (?, ?, ?, ?, ?, ?, ?)",
                registros)
            conn.commit()
            st.success("Chamada registrada com sucesso!")

elif menu == "Visualizar Chamadas":
    st.subheader("Chamadas Registradas")
    chamadas = pd.read_sql(
        "SELECT chamadas.Reuniao_ID, reunioes.Nome as Reuniao_Nome, reunioes.Data, chamadas.Unidade, chamadas.Membro, chamadas.Presenca, chamadas.Pontualidade, chamadas.Uniforme, chamadas.Modestia FROM chamadas JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID",
        conn)
    if not chamadas.empty:
        st.dataframe(chamadas)
    else:
        st.write("Nenhuma chamada registrada ainda.")

elif menu == "Relatórios":
    st.subheader("Relatórios Mensais por Unidade")
    chamadas = pd.read_sql("SELECT * FROM chamadas JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID", conn)
    chamadas['Data'] = pd.to_datetime(chamadas['Data'])
    chamadas['Mês'] = chamadas['Data'].dt.strftime('%Y-%m')

    unidades = chamadas['Unidade'].unique()
    for unidade in unidades:
        st.subheader(f"Unidade: {unidade}")
        df_unidade = chamadas[chamadas['Unidade'] == unidade]
        df_resumo = df_unidade.groupby('Mês')[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum().reset_index()
        df_resumo['Total Geral'] = df_resumo[['Presenca', 'Pontualidade', 'Uniforme', 'Modestia']].sum(axis=1)
        st.dataframe(df_resumo)

conn.close()