import pandas as pd
import streamlit as st


def mostrar_especialidades_usuario(conn, codigo_sgc):
    st.subheader("📌 Especialidades do Usuário")

    # Verifica se o código SGC foi passado
    if not codigo_sgc:
        st.warning("⚠️ Nenhum código SGC fornecido no payload.")
        return

    # Query para buscar especialidades vinculadas ao usuário
    query = """
        SELECT e.nome, e.codigo 
        FROM especialidades e
        JOIN user_especialidades eu ON e.codigo = eu.codigo_especialidade
        WHERE eu.codigo_sgc = ?
        """

    df_especialidades = pd.read_sql(query, conn, params=[codigo_sgc])

    # Exibir os dados
    if df_especialidades.empty:
        st.info("📌 Este usuário não possui especialidades cadastradas.")
    else:
        st.dataframe(df_especialidades)


def gerenciar_especialidades_usuario(conn):
    st.subheader("📌 Gerenciar Especialidades do Usuário")

    # Buscar usuários disponíveis
    usuarios = pd.read_sql("SELECT codigo_sgc, Nome FROM membros", conn)

    if usuarios.empty:
        st.warning("⚠️ Nenhum usuário encontrado.")
        return

    # Seleção do usuário
    usuario_selecionado = st.selectbox("Selecione um Usuário",
                                       usuarios["codigo_sgc"] + " - " + usuarios["Nome"], index=0)

    # Obter o código SGC real do usuário selecionado
    codigo_sgc = usuarios.loc[usuarios["codigo_sgc"] + " - " + usuarios["Nome"] == usuario_selecionado, "codigo_sgc"].values[0]

    # Buscar todas as especialidades disponíveis
    especialidades = pd.read_sql("SELECT codigo, nome FROM especialidades", conn)

    if especialidades.empty:
        st.warning("⚠️ Nenhuma especialidade encontrada.")
        return

    # Buscar especialidades que o usuário já possui
    especialidades_usuario = pd.read_sql(
        "SELECT codigo_especialidade FROM user_especialidades WHERE codigo_sgc = ?",
        conn, params=[codigo_sgc]
    )

    # Garantir que a lista de especialidades do usuário esteja no formato correto
    especialidades_usuario = set(str(cod) for cod in especialidades_usuario["codigo_especialidade"].tolist())

    # Criar dicionário para armazenar novas seleções
    selecoes = {}
    col1, col2, col3 = st.columns(3)
    c = [col1, col2, col3]
    i = 0

    especialidades["prefixo"] = especialidades["codigo"].str[:2]  # Pega as duas letras iniciais
    especialidades["numero"] = especialidades["codigo"].str[3:].astype(
        int)  # Pega os três números finais e converte para int

    # Ordenar pelo prefixo (XX) e depois pelo número (YYY)
    especialidades = especialidades.sort_values(by=["prefixo", "numero"]).drop(
        columns=["prefixo", "numero"])  # Remover colunas temporárias


    # Criar `st.radio()` para cada especialidade
    for _, row in especialidades.iterrows():
        with c[i]:  # Coluna I
            nome_especialidade = row["nome"]
            codigo_especialidade = str(row["codigo"])  # Converte para string

            # Verificar se o usuário já possui a especialidade
            selecionado = "Não" if codigo_especialidade in especialidades_usuario else "Sim"

            selecoes[codigo_especialidade] = st.radio(
                f"{nome_especialidade}",
                ["Sim", "Não"],
                index=["Não", "Sim"].index(selecionado),
                key=f"especialidade_{codigo_especialidade}"  # 🔹 Adicionado `key` único
            )
            i += 1
            if i > 2:
                i = 0

    # Atualizar banco de dados ao clicar no botão
    if st.button("💾 Salvar Alterações", key='save'):
        cursor = conn.cursor()

        for codigo_especialidade, resposta in selecoes.items():
            if resposta == "Sim" and codigo_especialidade not in especialidades_usuario:
                # Adicionar especialidade ao usuário
                cursor.execute("INSERT INTO user_especialidades (codigo_sgc, codigo_especialidade) VALUES (?, ?)",
                               (codigo_sgc, codigo_especialidade))
            elif resposta == "Não" and codigo_especialidade in especialidades_usuario:
                # Remover especialidade do usuário
                cursor.execute("DELETE FROM user_especialidades WHERE codigo_sgc = ? AND codigo_especialidade = ?",
                               (codigo_sgc, codigo_especialidade))

        conn.commit()
        st.success("✅ Especialidades atualizadas com sucesso!")
        st.rerun()