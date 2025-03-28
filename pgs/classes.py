import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, delete
from pgs.db import get_db, engine, tables


def mostrar_classes_usuario(codigo_sgc):

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    classe = tables.get("classe")
    user_classes = tables.get("user_classes")

    if classe is None or user_classes is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Classes do Usuário")

    # Verifica se o código SGC foi passado
    if not codigo_sgc:
        st.warning("⚠️ Nenhum código SGC fornecido no payload.")
        return

    with Session(engine) as session:
        # Query para buscar classes vinculadas ao usuário
        query = session.execute(
            select(classe.c.nome, classe.c.codigo)
            .join(user_classes, classe.c.codigo == user_classes.c.codigo_classe)
            .where(user_classes.c.codigo_sgc == codigo_sgc)
        ).fetchall()

        df_classes = pd.DataFrame(query, columns=["Nome", "Código"])

    # Exibir os dados
    if df_classes.empty:
        st.info("📌 Este usuário não possui classes cadastradas.")
    else:
        st.dataframe(df_classes)


def gerenciar_classes_usuario():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    classe = tables.get("classe")
    user_classes = tables.get("user_classes")

    if membros is None or classe is None or user_classes is None:
        st.error("❌ Algumas tabelas não foram encontradas no banco de dados.")
        return

    st.subheader("📌 Gerenciar Classes do Usuário")

    with Session(engine) as session:
        # Buscar usuários disponíveis
        usuarios_query = session.execute(select(membros.c.codigo_sgc, membros.c.nome)).fetchall()
        usuarios = pd.DataFrame(usuarios_query, columns=["codigo_sgc", "nome"])

    if usuarios.empty:
        st.warning("⚠️ Nenhum usuário encontrado.")
        return

    # Seleção do usuário (com `key` único para evitar duplicação)
    usuario_selecionado = st.selectbox(
        "Selecione um Usuário",
        usuarios["codigo_sgc"] + " - " + usuarios["nome"],
        index=0,
        key="selectbox_usuario_classes"
    )

    # Obter o código SGC real do usuário selecionado
    codigo_sgc = usuarios.loc[usuarios["codigo_sgc"] + " - " + usuarios["nome"] == usuario_selecionado, "codigo_sgc"].values[0]

    with Session(engine) as session:
        # Buscar todas as classes disponíveis
        classes_query = session.execute(select(classe.c.codigo, classe.c.nome)).fetchall()
        classes = pd.DataFrame(classes_query, columns=["codigo", "nome"])

        # Buscar classes que o usuário já possui
        classes_usuario_query = session.execute(
            select(user_classes.c.codigo_classe).where(user_classes.c.codigo_sgc == codigo_sgc)
        ).fetchall()
        classes_usuario = {str(c[0]) for c in classes_usuario_query}  # Converte para conjunto de strings

    if classes.empty:
        st.warning("⚠️ Nenhuma classe encontrada.")
        return

    # Criar dicionário para armazenar novas seleções
    selecoes = {}
    col1, col2, col3 = st.columns(3)
    colunas = [col1, col2, col3]
    i = 0

    # Criar `st.radio()` para cada classe
    for _, row in classes.iterrows():
        with colunas[i]:  # Alternar entre colunas
            nome_classe = row["nome"]
            codigo_classe = str(row["codigo"])

            # Define se a classe já pertence ao usuário
            selecionado = "Sim" if codigo_classe in classes_usuario else "Não"

            selecoes[codigo_classe] = st.radio(
                f"{nome_classe}",
                ["Sim", "Não"],
                index=["Sim", "Não"].index(selecionado),
                key=f"classe_{codigo_classe}"
            )

            i = (i + 1) % 3  # Alternar entre colunas (0, 1, 2)

    # Atualizar banco de dados ao clicar no botão
    if st.button("💾 Salvar Alterações", key='save_classes'):
        with Session(engine) as session:
            for codigo_classe, resposta in selecoes.items():
                if resposta == "Sim" and codigo_classe not in classes_usuario:
                    # Adicionar classe ao usuário
                    session.execute(
                        insert(user_classes).values(codigo_sgc=codigo_sgc, codigo_classe=codigo_classe)
                    )
                elif resposta == "Não" and codigo_classe in classes_usuario:
                    # Remover classe do usuário
                    session.execute(
                        delete(user_classes).where(
                            (user_classes.c.codigo_sgc == codigo_sgc) &
                            (user_classes.c.codigo_classe == codigo_classe)
                        )
                    )

            session.commit()
        st.success("✅ Classes atualizadas com sucesso!")
        st.rerun()