import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, insert, update
from sqlalchemy.exc import IntegrityError
from pgs.db import get_db, engine, tables


def registrar_chamada():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    reunioes = tables.get("reunioes")
    unidades = tables.get("unidades")
    membros = tables.get("membros")
    chamadas = tables.get("chamadas")

    if reunioes is None or unidades is None or membros is None or chamadas is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    with Session(engine) as session:
        reunioes_df = pd.DataFrame(session.execute(select(reunioes)).fetchall(), columns=reunioes.columns.keys())
        unidades_df = pd.DataFrame(session.execute(select(unidades)).fetchall(), columns=unidades.columns.keys())

    reuniao = st.selectbox("Reunião", reunioes_df["nome"] if not reunioes_df.empty else [])
    unidade_nome = st.selectbox("Unidade", unidades_df["nome"] if not unidades_df.empty else [])

    if reuniao and unidade_nome:
        reuniao_id = int(reunioes_df.loc[reunioes_df["nome"] == reuniao, "id"].values[0])
        unidade_id = int(unidades_df.loc[unidades_df["nome"] == unidade_nome, "id"].values[0])

        with Session(engine) as session:
            membros_unidade = pd.DataFrame(session.execute(
                select(membros.c.nome, membros.c.cargo)
                .where(membros.c.id_unidade == unidade_id)
                .order_by(membros.c.cargo, membros.c.nome)
            ).fetchall(), columns=["nome", "cargo"])

        membros_por_cargo = {}
        for _, row in membros_unidade.iterrows():
            cargo = row["cargo"] if row["cargo"] else "Sem Cargo"
            membros_por_cargo.setdefault(cargo, []).append(row["nome"])

        registros = []

        for cargo, membros_lista in membros_por_cargo.items():
            st.markdown(f"### {cargo}")

            for nome in membros_lista:
                st.subheader(nome)

                with Session(engine) as session:
                    chamada_existente = session.execute(
                        select(chamadas.c.presenca, chamadas.c.pontualidade, chamadas.c.uniforme, chamadas.c.modestia)
                        .where(chamadas.c.reuniao_id == reuniao_id)
                        .where(chamadas.c.id_unidade == unidade_id)
                        .where(chamadas.c.membro == nome)
                    ).fetchone()

                presenca_valor, pontualidade_valor, uniforme_valor, modestia_valor = chamada_existente or (0, 0, 0, 0)

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
            with Session(engine) as session:
                for r in registros:
                    chamada_existente = session.execute(
                        select(chamadas.c.id)
                        .where(chamadas.c.reuniao_id == r[0])
                        .where(chamadas.c.id_unidade == r[1])
                        .where(chamadas.c.membro == r[2])
                    ).fetchone()

                    if chamada_existente:
                        stmt = update(chamadas).where(chamadas.c.id == chamada_existente[0]).values(
                            presenca=r[3], pontualidade=r[4], uniforme=r[5], modestia=r[6]
                        )
                    else:
                        stmt = insert(chamadas).values(
                            reuniao_id=r[0], id_unidade=r[1], membro=r[2], presenca=r[3],
                            pontualidade=r[4], uniforme=r[5], modestia=r[6]
                        )

                    session.execute(stmt)

                session.commit()
                st.success("✅ Chamada registrada/atualizada com sucesso!")
                st.rerun()


def visualizar_chamada():

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
                chamadas.c.membro,
                chamadas.c.id_unidade,
                unidades.c.nome.label("Unidade_Nome")
            ).join(reunioes, chamadas.c.reuniao_id == reunioes.c.id)
             .join(unidades, chamadas.c.id_unidade == unidades.c.id)
        ).fetchall()

        chamadas_df = pd.DataFrame(chamadas_query, columns=["ID", "Reuniao_ID", "Reuniao_Nome", "Membro", "id_unidade", "Unidade_Nome"])

    st.subheader("📌 Chamadas Registradas")

    if not chamadas_df.empty:
        st.dataframe(chamadas_df)
    else:
        st.info("ℹ️ Nenhuma chamada registrada ainda.")








