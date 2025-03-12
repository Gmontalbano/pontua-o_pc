import streamlit as st
from datetime import datetime
import pandas as pd
import sqlite3

from utils.hashes import make_hashes
from pgs.db import conect_db


def cadastro_reuniao():
    conn, c = conect_db()
    st.subheader("Cadastro de Reunião")
    nome = st.text_input("Nome da Reunião")
    data = st.date_input("Data", value=datetime.today())
    if st.button("Cadastrar Reunião"):
        c.execute("INSERT INTO reunioes (nome, data) VALUES (%s, %s)", (nome, data))
        conn.commit()
        st.success("Reunião cadastrada com sucesso!")
    c.close()
    conn.close()


def delete_reuniao():
    conn, cursor = conect_db()
    st.subheader("📅 Gerenciar Reuniões")

    # Buscar reuniões existentes
    try:
        cursor.execute("SELECT id, nome, data FROM reunioes")
        reunioes = cursor.fetchall()


        if reunioes:
            reuniao_selecionada = st.selectbox(
                "Selecione a reunião:",
                reunioes,
                format_func=lambda x: f"{x[1]} ({x[2]}) - ID {x[0]}"
            )

            # Campos para edição
            novo_nome = st.text_input("Novo Nome", reuniao_selecionada[1])
            nova_data = st.date_input("Nova Data", pd.to_datetime(reuniao_selecionada[2]))

            col1, col2 = st.columns(2)

            # Botão para salvar alterações
            if col1.button("💾 Salvar Alterações"):
                cursor.execute("UPDATE reunioes SET nome = %s, data = %s WHERE id = %s",
                               (novo_nome, nova_data, reuniao_selecionada[0]))
                conn.commit()
                st.success(f"✅ Reunião '{novo_nome}' atualizada com sucesso!")
                st.rerun()

            # Botão para excluir reunião
            if col2.button("❌ Excluir Reunião"):
                cursor.execute("DELETE FROM reunioes WHERE id = %s", (reuniao_selecionada[0],))
                conn.commit()
                st.warning(f"⚠️ Reunião '{reuniao_selecionada[1]}' foi excluída!")
                st.rerun()

        else:
            st.info("📌 Nenhuma reunião encontrada.")
    except Exception as e:
        print(f"Erro ao executar consulta: {e}")
    cursor.close()
    conn.close()


def cadastro_unidade():
    conn, c = conect_db()
    st.subheader("Cadastro de Unidade")
    nome = st.text_input("Nome da Unidade")
    if st.button("Cadastrar Unidade"):
        c.execute("INSERT INTO unidades (nome) VALUES (%s)", (nome,))
        conn.commit()
        st.success("Unidade cadastrada com sucesso!")
    c.close()
    conn.close()


def cadastro_membro():
    conn, c = conect_db()
    st.subheader("Cadastro de Membro")

    # Buscar unidades com ID e Nome
    unidades = pd.read_sql("SELECT id, nome FROM unidades", conn)

    nome = st.text_input("Nome do Membro")
    unidade_nome = st.selectbox("Unidade", unidades['nome'].tolist() if not unidades.empty else [], key='unidade_nome')
    codigo_sgc = st.text_input("Código SGC")  # Novo campo para inserir o código SGC
    cargo = st.selectbox("Cargo", ['Conselheiro(a)', 'Desbravador(a)', 'Diretor(a) Associado(a)', 'Secretário(a)', 'Instrutor', 'Apoio', 'Tesoureiro(a)'], key="Cargo")

    if st.button("Cadastrar Membro"):
        if unidade_nome and codigo_sgc:
            # Pegar o ID da unidade correspondente ao nome selecionado
            unidade_id = int(unidades[unidades['nome'] == unidade_nome]['id'].values[0])

            # Inserir o membro no banco
            c.execute("INSERT INTO membros (nome, id_unidade, codigo_sgc, cargo) VALUES (%s, %s, %s, %s)",
                      (nome, unidade_id, codigo_sgc, cargo))
            conn.commit()

            st.success(f"Membro '{nome}' cadastrado com sucesso com código SGC {codigo_sgc}!")
            st.rerun()  # Atualiza a tela para mostrar o novo membro
        else:
            st.warning("⚠️ Preencha todos os campos corretamente.")
    c.close()
    conn.close()


def delete_membro():
    conn, cursor = conect_db()
    # Buscar membros com nome da unidade e codigo_sgc
    membros = pd.read_sql("""
        SELECT membros.ID, membros.nome, membros.codigo_sgc, membros.cargo, unidades.nome as Unidade 
        FROM membros 
        JOIN unidades ON membros.id_unidade = unidades.id
    """, conn)

    if not membros.empty:
        membro_dict = {f"{row['nome']} ({row['unidade']})": row["id"] for _, row in membros.iterrows()}
        membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()))

        membro_id = membro_dict[membro_selecionado]
        membro_info = membros[membros["id"] == membro_id].iloc[0]

        # Campos de edição
        novo_nome = st.text_input("Nome", membro_info["nome"])
        novo_codigo_sgc = st.text_input("Código SGC", membro_info["codigo_sgc"])  # Adicionado para edição do código
        # Se `cargo` for None, define como "Selecione um cargo"
        cargo_atual = membro_info["cargo"] if membro_info["cargo"] is not None else "Selecione um cargo"

        # Lista de opções disponíveis
        cargos_disponiveis = [
            "Selecione um cargo", "Conselheiro(a)", "Desbravador(a)", "Diretor(a) Associado(a)",
            "Secretário(a)", "Instrutor", "Apoio", "Tesoureiro(a)"
        ]

        # Criar o `selectbox` garantindo que sempre haverá um valor selecionado
        novo_cargo = st.selectbox("Cargo", cargos_disponiveis,
                                  index=cargos_disponiveis.index(
                                      cargo_atual) if cargo_atual in cargos_disponiveis else 0,
                                  key="Cargo_novo")

        unidades = membros['unidade'].unique()
        indice_unidade = list(unidades).index(membro_info['unidade'])

        nova_unidade = st.selectbox("Unidade", unidades, index=indice_unidade)

        b1, b2 = st.columns(2)

        # **Salvar Alterações**
        if b1.button("💾 Salvar Alterações", key='Alterar'):
            nova_unidade_id = int(pd.read_sql(
                "SELECT ID FROM unidades WHERE nome = %s", conn, params=[nova_unidade]
            )['ID'].values[0])

            # 🔹 **Atualizar também a coluna `cargo`**
            cursor.execute("UPDATE membros SET nome = %s, codigo_sgc = %s, id_unidade = %s, cargo = %s WHERE ID = %s",
                           (novo_nome, novo_codigo_sgc, nova_unidade_id, novo_cargo, membro_id))
            conn.commit()
            st.success(f"✅ Membro '{novo_nome}' atualizado com sucesso!")
            st.rerun()

        # **Excluir Membro**
        if b2.button("❌ Excluir Membro", key='Deletar'):
            cursor.execute("DELETE FROM membros WHERE id = %s", (membro_id,))
            conn.commit()
            st.warning(f"⚠️ Membro '{membro_info['Nome']}' foi excluído!")
            st.rerun()

    else:
        st.warning("📌 Nenhum membro encontrado para editar ou excluir.")
    cursor.close()
    conn.close()


def gerenciar_usuarios():
    conn, c = conect_db()
    st.subheader("📌 Gerenciar Usuários")

    # Buscar membros disponíveis (Nome e codigo_sgc)
    membros = pd.read_sql("SELECT nome, codigo_sgc FROM membros", conn)

    if membros.empty:
        st.warning("⚠️ Nenhum membro encontrado. Cadastre um membro antes de criar um usuário.")
        return  # Interrompe a execução se não houver membros

    # Criar lista formatada para exibir nome + código SGC
    membros["Display"] = membros["codigo_sgc"] + " - " + membros["nome"]

    # Seleção do membro pelo código SGC
    membro_selecionado = st.selectbox("Selecione o Membro", membros["Display"], index=0)

    # Obter o código SGC real do membro selecionado
    codigo_sgc = membros.loc[membros["Display"] == membro_selecionado, "codigo_sgc"].values[0]

    # Verificar se o usuário já existe na tabela `usuarios`
    usuario_existente = pd.read_sql("SELECT id, login, permissao FROM usuarios WHERE codigo_sgc = %s", conn, params=[codigo_sgc])

    col1, col2 = st.columns(2)  # Criar duas colunas para organizar os botões

    if not usuario_existente.empty:
        st.warning("⚠️ Este membro já tem um usuário cadastrado. Você pode editar ou excluir abaixo.")

        usuario_id = usuario_existente["id"].values[0]
        login = st.text_input("Login", usuario_existente["login"].values[0])
        senha = st.text_input("Senha (Deixe em branco para manter a atual)", type="password")
        permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho", "admin"],
                                 index=["equipe", "associado", "conselho", "admin"].index(usuario_existente["permissao"].values[0]))

        if col1.button("💾 Salvar Alterações", key=f"salvar_{usuario_id}"):
            if senha:  # Se uma nova senha foi inserida, atualiza com hash
                senha_hash = make_hashes(senha)
                c.execute("UPDATE usuarios SET login = %s, senha = %s, permissao = %s WHERE codigo_sgc = %s",
                          (login, senha_hash, permissao, codigo_sgc))
            else:  # Mantém a senha atual
                c.execute("UPDATE usuarios SET login = %s, permissao = %s WHERE codigo_sgc = %s",
                          (login, permissao, codigo_sgc))

            conn.commit()
            st.success(f"✅ Usuário atualizado com sucesso!")
            st.rerun()

        if col2.button("❌ Excluir Usuário", key=f"excluir_{usuario_id}"):
            c.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
            conn.commit()
            st.warning(f"⚠️ Usuário foi excluído!")
            st.rerun()

    else:  # Se o usuário não existir, exibe os campos para cadastro
        st.subheader("✅ Cadastrar Novo Usuário")
        login = st.text_input("Login")
        senha = st.text_input("Senha", type="password")
        permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho"])

        if st.button("Cadastrar Usuário", key="cadastrar_usuario"):
            if codigo_sgc and login and senha:
                try:
                    senha_hash = make_hashes(senha)
                    c.execute("INSERT INTO usuarios (codigo_sgc, login, senha, permissao) VALUES (%s, %s, %s, %s)",
                              (codigo_sgc, login, senha_hash, permissao))
                    conn.commit()
                    st.success(f"✅ Usuário cadastrado com sucesso para o membro {membro_selecionado}!")

                except sqlite3.IntegrityError:
                    st.error("❌ Este login já está cadastrado. Escolha outro.")

                except sqlite3.Error as e:
                    st.error(f"❌ Erro do banco de dados: {str(e)}")

                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")

            else:
                st.warning("⚠️ Preencha todos os campos!")
    c.close()
    conn.close()
