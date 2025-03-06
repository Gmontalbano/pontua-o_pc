import streamlit as st
import pandas as pd


def registrar_chamada(c, conn):
    st.subheader("Registrar Chamada")

    # Buscar reuniões e unidades
    reunioes = pd.read_sql("SELECT * FROM reunioes", conn)
    unidades = pd.read_sql("SELECT ID, Nome FROM unidades", conn)

    reuniao = st.selectbox("Reunião", reunioes['Nome'] if not reunioes.empty else [])
    unidade_nome = st.selectbox("Unidade", unidades['Nome'] if not unidades.empty else [])

    if reuniao and unidade_nome:
        reuniao_id = int(reunioes[reunioes['Nome'] == reuniao]['ID'].values[0])
        unidade_id = int(unidades[unidades['Nome'] == unidade_nome]['ID'].values[0])

        # Buscar membros da unidade correta, incluindo o cargo
        membros_unidade = pd.read_sql(f"""
            SELECT Nome, cargo FROM membros WHERE id_unidade = {unidade_id} ORDER BY cargo, Nome
        """, conn)

        # Criar um dicionário para agrupar os membros pelo cargo
        membros_por_cargo = {}
        for _, row in membros_unidade.iterrows():
            cargo = row["cargo"] if row["cargo"] else "Sem Cargo"  # Tratamento para cargos vazios
            if cargo not in membros_por_cargo:
                membros_por_cargo[cargo] = []
            membros_por_cargo[cargo].append(row["Nome"])

        registros = []

        # Exibir cada grupo de membros conforme o cargo
        for cargo, membros in membros_por_cargo.items():
            st.markdown(f"### {cargo}")  # Título para cada cargo

            for nome in membros:
                st.subheader(nome)

                # 🔹 Buscar chamada existente para este membro, reunião e unidade
                chamada_existente = pd.read_sql(f"""
                    SELECT Presenca, Pontualidade, Uniforme, Modestia
                    FROM chamadas
                    WHERE Reuniao_ID = {reuniao_id} 
                    AND id_unidade = {unidade_id} 
                    AND Membro = '{nome}'
                """, conn)

                # 🔹 Preencher com valores já existentes ou padrão 0
                if not chamada_existente.empty:
                    presenca_valor = chamada_existente['Presenca'].values[0]
                    pontualidade_valor = chamada_existente['Pontualidade'].values[0]
                    uniforme_valor = chamada_existente['Uniforme'].values[0]
                    modestia_valor = chamada_existente['Modestia'].values[0]
                else:
                    presenca_valor = 0
                    pontualidade_valor = 0
                    uniforme_valor = 0
                    modestia_valor = 0

                col1, col2, col3, col4 = st.columns(4)
                presenca_toggle = col1.toggle("Presença", value=presenca_valor == 10, key=f"presenca_{nome}")
                presenca = 10 if presenca_toggle else 0
                pontualidade = col2.number_input('Pontualidade', min_value=0, max_value=10, step=5,
                                                 value=pontualidade_valor, key=f"pontualidade_{nome}")
                uniforme = col3.number_input('Uniforme', min_value=0, max_value=10, step=5,
                                             value=uniforme_valor, key=f"uniforme_{nome}")
                modestia = col4.number_input('Modéstia', min_value=0, max_value=10, step=5,
                                             value=modestia_valor, key=f"modestia_{nome}")

                registros.append((reuniao_id, unidade_id, nome, presenca, pontualidade, uniforme, modestia))

        if st.button("Salvar Chamada"):
            for r in registros:
                # Verifica se a chamada já existe
                c.execute("""
                    SELECT COUNT(*) FROM chamadas 
                    WHERE Reuniao_ID = ? AND id_unidade = ? AND Membro = ?
                """, (r[0], r[1], r[2]))

                existe = c.fetchone()[0]

                if existe:
                    # Atualiza os dados existentes
                    c.execute("""
                        UPDATE chamadas 
                        SET Presenca = ?, Pontualidade = ?, Uniforme = ?, Modestia = ? 
                        WHERE Reuniao_ID = ? AND id_unidade = ? AND Membro = ?
                    """, (r[3], r[4], r[5], r[6], r[0], r[1], r[2]))
                else:
                    # Insere um novo registro
                    c.execute("""
                        INSERT INTO chamadas (Reuniao_ID, id_unidade, Membro, Presenca, Pontualidade, Uniforme, Modestia) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, r)

            conn.commit()
            st.success("Chamada registrada/atualizada com sucesso!")
            st.rerun()



def visualizar_chamada(conn):
    st.subheader("Chamadas Registradas")
    chamadas = pd.read_sql(
        """SELECT chamadas.ID, 
       chamadas.Reuniao_ID, 
       reunioes.Nome as Reuniao_Nome, 
       chamadas.Membro, 
       chamadas.id_unidade,
       unidades.Nome as Unidade_Nome
        FROM chamadas 
        JOIN reunioes ON chamadas.Reuniao_ID = reunioes.ID
        JOIN unidades ON chamadas.id_unidade = unidades.ID
        """,
        conn)
    if not chamadas.empty:
        st.dataframe(chamadas)
    else:
        st.write("Nenhuma chamada registrada ainda.")









