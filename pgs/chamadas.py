import streamlit as st
import pandas as pd

def registrar_chamada(c, conn):
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
            col1, col2, col3, col4 = st.columns(4)

            on = col1.toggle("Presença", key=f"presenca_{row['Nome']}")
            if on:
                presenca = 10
                pontualidade = col2.number_input('Pontualidade', min_value=0, max_value=10, step=5,\
                                               key=f"pontualidade_{row['Nome']}")
                uniforme = col3.number_input('Uniforme', min_value=0, max_value=10, step=5,
                                               key=f"uniforme_{row['Nome']}")
                modestia = col4.number_input('Modéstia', min_value=0, max_value=10, step=5,
                                               key=f"modestia_{row['Nome']}")
            else:
                presenca = 0
                pontualidade = 0
                uniforme = 0
                modestia = 0

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


def visualizar_chamada(conn):
    st.subheader("Chamadas Registradas")
    chamadas = pd.read_sql(
        "SELECT chamadas.Reuniao_ID, reunioes.Nome as Reuniao_Nome, reunioes.Data, chamadas.Unidade, chamadas.Membro, chamadas.Presenca, chamadas.Pontualidade, chamadas.Uniforme, chamadas.Modestia FROM chamadas JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID",
        conn)
    if not chamadas.empty:
        st.dataframe(chamadas)
    else:
        st.write("Nenhuma chamada registrada ainda.")


def delete(cursor, conn):
    aba = st.radio("Selecione uma opção:", ["Excluir Chamada", "Excluir Reunião", "Unidades", "Membros"])

    # 📌 **Excluir uma chamada específica**
    if aba == "Excluir Chamada":
        st.subheader("🗑️ Excluir Chamada")
        chamadas = pd.read_sql("""
            SELECT chamadas.ID, 
                   chamadas.Reuniao_ID, 
                   reunioes.Nome as Reuniao_Nome, 
                   chamadas.Membro, 
                   chamadas.Unidade 
            FROM chamadas 
            JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID
        """, conn)
        chamadas_lista = list(chamadas.itertuples(index=False, name=None))
        # Buscar chamadas existentes
        if chamadas_lista:  # Garante que há chamadas antes de exibir o selectbox
            chamada_selecionada = st.selectbox(
                "Selecione a chamada para excluir:",
                chamadas_lista,
                format_func=lambda x: f"ID {x[0]} - Membro {x[3]} - Unidade {x[4]} (Reunião {x[2]})"
            )

            if st.button("Excluir Chamada"):
                cursor.execute("DELETE FROM chamadas WHERE ID = ?", (chamada_selecionada[0],))
                conn.commit()
                st.success(f"✅ Chamada ID {chamada_selecionada[0]} excluída com sucesso!")
                st.rerun()
        else:
            st.info("📌 Nenhuma chamada encontrada.")

    # 📌 **Excluir uma reunião e suas chamadas associadas**
    elif aba == "Excluir Reunião":
        st.subheader("🗑️ Excluir Reunião e suas Chamadas")

        # Buscar reuniões existentes
        reunioes = cursor.execute("SELECT ID, Nome, Data FROM reunioes").fetchall()
        if reunioes:
            reuniao_selecionada = st.selectbox("Selecione a reunião para excluir:",
                                               reunioes,
                                               format_func=lambda x: f"{x[1]} ({x[2]}) - ID {x[0]}")

            if st.button("Excluir Reunião"):
                cursor.execute("DELETE FROM reunioes WHERE ID = ?", (reuniao_selecionada[0],))
                conn.commit()
                st.warning(f"⚠️ Reunião '{reuniao_selecionada[1]}' e todas as chamadas associadas foram excluídas!")
                st.rerun()
        else:
            st.info("📌 Nenhuma reunião encontrada.")
    elif aba == 'Unidades':
        # Buscar unidades cadastradas na tabela "unidades"
        unidades = pd.read_sql("SELECT ID, Nome FROM unidades", conn)

        if not unidades.empty:
            # Criar lista de seleção com ID e Nome da unidade
            unidade_dict = {row["Nome"]: row["ID"] for _, row in unidades.iterrows()}
            unidade_selecionada = st.selectbox("Selecione a unidade para excluir:", list(unidade_dict.keys()))

            if st.button("Excluir Unidade"):
                unidade_id = unidade_dict[unidade_selecionada]  # Obter ID da unidade selecionada
                cursor.execute("DELETE FROM unidades WHERE ID = ?", (unidade_id,))
                conn.commit()
                st.success(f"Unidade '{unidade_selecionada}' excluída com sucesso!")

        else:
            st.warning("Nenhuma unidade encontrada para excluir.")
    elif aba == 'Membros':
        # Buscar membros cadastrados
        membros = pd.read_sql("SELECT ID, Nome, Unidade FROM membros", conn)

        if not membros.empty:
            # Criar dicionário de membros para seleção
            membro_dict = {f"{row['Nome']} ({row['Unidade']})": row["ID"] for _, row in membros.iterrows()}
            membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()))

            membro_id = membro_dict[membro_selecionado]  # Obter ID do membro selecionado

            # Buscar informações do membro selecionado
            membro_info = membros[membros["ID"] == membro_id].iloc[0]
            novo_nome = st.text_input("Nome", membro_info["Nome"])
            nova_unidade = st.text_input("Unidade", membro_info["Unidade"])

            # Botão para atualizar membro
            if st.button("Salvar Alterações"):
                cursor.execute("UPDATE membros SET Nome = ?, Unidade = ? WHERE ID = ?",
                               (novo_nome, nova_unidade, membro_id))
                conn.commit()
                st.success(f"Membro '{novo_nome}' atualizado com sucesso!")
                st.rerun()

            # Botão para excluir membro
            if st.button("Excluir Membro"):
                cursor.execute("DELETE FROM membros WHERE ID = ?", (membro_id,))
                conn.commit()
                st.success(f"Membro '{membro_info['Nome']}' excluído com sucesso!")
                st.rerun()

        else:
            st.warning("Nenhum membro encontrado para editar ou excluir.")

