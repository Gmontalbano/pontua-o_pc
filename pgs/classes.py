import pandas as pd
import streamlit as st


def mostrar_classes_usuario(conn, codigo_sgc):
    st.subheader("📌 Classes do Usuário")

    # Verifica se o código SGC foi passado
    if not codigo_sgc:
        st.warning("⚠️ Nenhum código SGC fornecido no payload.")
        return

    # Query para buscar classes vinculadas ao usuário
    query = """
        SELECT c.nome, c.codigo 
        FROM classe c
        JOIN user_classes uc ON c.codigo = uc.codigo_classe
        WHERE uc.codigo_sgc = ?
    """

    df_classes = pd.read_sql(query, conn, params=[codigo_sgc])

    # Exibir os dados
    if df_classes.empty:
        st.info("📌 Este usuário não possui classes cadastradas.")
    else:
        st.dataframe(df_classes)


def gerenciar_classes_usuario(conn):
    st.subheader("📌 Gerenciar Classes do Usuário")

    # Buscar usuários disponíveis
    usuarios = pd.read_sql("SELECT codigo_sgc, Nome FROM membros", conn)

    if usuarios.empty:
        st.warning("⚠️ Nenhum usuário encontrado.")
        return

    # Seleção do usuário (com `key` único para evitar duplicação)
    usuario_selecionado = st.selectbox(
        "Selecione um Usuário",
        usuarios["codigo_sgc"] + " - " + usuarios["Nome"],
        index=0,
        key="selectbox_usuario_classes"  # 🔹 Identificador único para evitar erro
    )

    # Obter o código SGC real do usuário selecionado
    codigo_sgc = usuarios.loc[usuarios["codigo_sgc"] + " - " + usuarios["Nome"] == usuario_selecionado, "codigo_sgc"].values[0]

    # Buscar todas as classes disponíveis
    classes = pd.read_sql("SELECT codigo, nome FROM classe", conn)

    if classes.empty:
        st.warning("⚠️ Nenhuma classe encontrada.")
        return

    # Buscar classes que o usuário já possui
    classes_usuario = pd.read_sql(
        "SELECT codigo_classe FROM user_classes WHERE codigo_sgc = ?",
        conn, params=[codigo_sgc]
    )

    # Garantir que a lista de classes do usuário esteja no formato correto
    classes_usuario = set(str(cod) for cod in classes_usuario["codigo_classe"].tolist())

    # Criar dicionário para armazenar novas seleções
    selecoes = {}
    col1, col2, col3 = st.columns(3)
    c = [col1, col2, col3]
    i = 0
    # Criar `st.radio()` para cada classe
    for _, row in classes.iterrows():
        with c[i]:  # Coluna I
            nome_classe = row["nome"]
            codigo_classe = str(row["codigo"])  # Converte para string

            # 🔹 Se o usuário tem a classe, seleciona "Sim"; caso contrário, deixa em "Selecione"
            selecionado = "Sim" if codigo_classe in classes_usuario else "Não"
            selecoes[codigo_classe] = st.radio(
                f"{nome_classe}",
                ["Sim", "Não"],  # 🔹 Adiciona a opção "Selecione"
                index=["Sim", "Não"].index(selecionado),
                key=f"classe_{codigo_classe}"  # 🔹 Adicionado `key` único
            )
            i += 1
            if i > 2:
                i = 0

    # Atualizar banco de dados ao clicar no botão
    if st.button("💾 Salvar Alterações", key='save_classes'):
        cursor = conn.cursor()

        for codigo_classe, resposta in selecoes.items():
            if resposta == "Sim" and codigo_classe not in classes_usuario:
                # Adicionar classe ao usuário
                cursor.execute("INSERT INTO user_classes (codigo_sgc, codigo_classe) VALUES (?, ?)",
                               (codigo_sgc, codigo_classe))
            elif resposta == "Não" and codigo_classe in classes_usuario:
                # Remover classe do usuário
                cursor.execute("DELETE FROM user_classes WHERE codigo_sgc = ? AND codigo_classe = ?",
                               (codigo_sgc, codigo_classe))

        conn.commit()
        st.success("✅ Classes atualizadas com sucesso!")
        st.rerun()