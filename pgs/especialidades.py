import pandas as pd
import streamlit as st
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, insert
from pgs.db import get_db, engine, tables


def mostrar_especialidades_usuario(codigo_sgc):

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    especialidades = tables.get("especialidades")
    user_especialidades = tables.get("user_especialidades")

    if especialidades is None or user_especialidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    with Session(engine) as session:
        query = session.execute(
            select(
                especialidades.c.nome,
                especialidades.c.codigo
            ).join(user_especialidades, especialidades.c.codigo == user_especialidades.c.codigo_especialidade)
             .where(user_especialidades.c.codigo_sgc == codigo_sgc)
        ).fetchall()

        df_especialidades = pd.DataFrame(query, columns=["Nome", "Código"])

    st.subheader("📌 Especialidades do Usuário")

    if not df_especialidades.empty:
        st.dataframe(df_especialidades)
    else:
        st.info("ℹ️ Este usuário não possui especialidades cadastradas.")


def gerenciar_especialidades_usuario():
    """Gerencia as especialidades de um usuário, garantindo transações seguras."""

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    especialidades = tables.get("especialidades")
    user_especialidades = tables.get("user_especialidades")

    if membros is None or especialidades is None or user_especialidades is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    with Session(engine) as session:
        # Buscar usuários disponíveis
        usuarios_query = session.execute(select(membros.c.codigo_sgc, membros.c.nome)).fetchall()
        usuarios_df = pd.DataFrame(usuarios_query, columns=["codigo_sgc", "nome"])

        if usuarios_df.empty:
            st.warning("⚠️ Nenhum usuário encontrado.")
            return

        # Seleção do usuário
        usuario_selecionado = st.selectbox(
            "Selecione um Usuário",
            usuarios_df["codigo_sgc"] + " - " + usuarios_df["nome"],
            index=0
        )

        # Obter o código SGC real do usuário selecionado
        codigo_sgc = usuarios_df.loc[
            usuarios_df["codigo_sgc"] + " - " + usuarios_df["nome"] == usuario_selecionado, "codigo_sgc"
        ].values[0]

        # Buscar todas as especialidades disponíveis
        especialidades_query = session.execute(select(especialidades.c.codigo, especialidades.c.nome)).fetchall()
        especialidades_df = pd.DataFrame(especialidades_query, columns=["codigo", "nome"])

        if especialidades_df.empty:
            st.warning("⚠️ Nenhuma especialidade encontrada.")
            return

        # Buscar especialidades que o usuário já possui
        especialidades_usuario_query = session.execute(
            select(user_especialidades.c.codigo_especialidade).where(user_especialidades.c.codigo_sgc == codigo_sgc)
        ).fetchall()

        especialidades_usuario = set(str(cod[0]) for cod in especialidades_usuario_query)

        # Criar dicionário para armazenar novas seleções
        selecoes = {}
        col1, col2, col3 = st.columns(3)
        c = [col1, col2, col3]
        i = 0

        # Ordenar especialidades por prefixo e número
        especialidades_df["prefixo"] = especialidades_df["codigo"].str[:2]
        especialidades_df["numero"] = especialidades_df["codigo"].str[3:].astype(int)
        especialidades_df = especialidades_df.sort_values(by=["prefixo", "numero"]).drop(columns=["prefixo", "numero"])

        # Criar opções de seleção
        for _, row in especialidades_df.iterrows():
            with c[i]:
                nome_especialidade = row["nome"]
                codigo_especialidade = str(row["codigo"])

                # Verificar se o usuário já possui a especialidade
                selecionado = "Não" if codigo_especialidade in especialidades_usuario else "Sim"

                selecoes[codigo_especialidade] = st.radio(
                    f"{nome_especialidade}",
                    ["Sim", "Não"],
                    index=["Não", "Sim"].index(selecionado),
                    key=f"especialidade_{codigo_especialidade}"
                )
                i += 1
                if i > 2:
                    i = 0

        # Atualizar banco de dados ao clicar no botão
        if st.button("💾 Salvar Alterações", key='save'):
            try:
                # Adicionar ou remover especialidades
                for codigo_especialidade, resposta in selecoes.items():
                    if resposta == "Sim" and codigo_especialidade not in especialidades_usuario:
                        # Adicionar especialidade ao usuário
                        session.execute(insert(user_especialidades).values(
                            codigo_sgc=codigo_sgc, codigo_especialidade=codigo_especialidade
                        ))
                    elif resposta == "Não" and codigo_especialidade in especialidades_usuario:
                        # Remover especialidade do usuário
                        session.execute(delete(user_especialidades).where(
                            (user_especialidades.c.codigo_sgc == codigo_sgc) &
                            (user_especialidades.c.codigo_especialidade == codigo_especialidade)
                        ))

                session.commit()  # ✅ Confirma todas as alterações no banco
                st.success("✅ Especialidades atualizadas com sucesso!")
                st.rerun()

            except Exception as e:
                session.rollback()  # ❌ Reverte mudanças em caso de erro
                st.error(f"❌ Erro ao atualizar especialidades: {e}")
