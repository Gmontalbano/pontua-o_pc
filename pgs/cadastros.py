import streamlit as st
from datetime import datetime
import pandas as pd
import sqlite3

from utils.hashes import make_hashes


def cadastro_reuniao(c, conn):
    st.subheader("Cadastro de Reunião")
    nome = st.text_input("Nome da Reunião")
    data = st.date_input("Data", value=datetime.today())
    if st.button("Cadastrar Reunião"):
        c.execute("INSERT INTO reunioes (Nome, Data) VALUES (?, ?)", (nome, data))
        conn.commit()
        st.success("Reunião cadastrada com sucesso!")

def delete_reuniao(cursor, conn):
    st.subheader("📅 Gerenciar Reuniões")

    # Buscar reuniões existentes
    reunioes = cursor.execute("SELECT ID, Nome, Data FROM reunioes").fetchall()

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
            cursor.execute("UPDATE reunioes SET Nome = ?, Data = ? WHERE ID = ?",
                           (novo_nome, nova_data, reuniao_selecionada[0]))
            conn.commit()
            st.success(f"✅ Reunião '{novo_nome}' atualizada com sucesso!")
            st.rerun()

        # Botão para excluir reunião
        if col2.button("❌ Excluir Reunião"):
            cursor.execute("DELETE FROM reunioes WHERE ID = ?", (reuniao_selecionada[0],))
            conn.commit()
            st.warning(f"⚠️ Reunião '{reuniao_selecionada[1]}' foi excluída!")
            st.rerun()

    else:
        st.info("📌 Nenhuma reunião encontrada.")

def cadastro_unidade(c, conn):
    st.subheader("Cadastro de Unidade")
    nome = st.text_input("Nome da Unidade")
    if st.button("Cadastrar Unidade"):
        c.execute("INSERT INTO unidades (Nome) VALUES (?)", (nome,))
        conn.commit()
        st.success("Unidade cadastrada com sucesso!")


def cadastro_membro(c, conn):
    st.subheader("Cadastro de Membro")

    # Buscar unidades com ID e Nome
    unidades = pd.read_sql("SELECT ID, Nome FROM unidades", conn)

    nome = st.text_input("Nome do Membro")
    unidade_nome = st.selectbox("Unidade", unidades['Nome'].tolist() if not unidades.empty else [], key='unidade_nome')

    if st.button("Cadastrar Membro"):
        if unidade_nome:
            # Pegar o ID da unidade correspondente ao nome selecionado
            unidade_id = int(unidades[unidades['Nome'] == unidade_nome]['ID'].values[0])

            # Inserir o membro no banco
            c.execute("INSERT INTO membros (Nome, id_unidade) VALUES (?, ?)", (nome, unidade_id))
            conn.commit()

            st.success(f"Membro '{nome}' cadastrado com sucesso!")
            st.rerun()  # Atualiza a tela para mostrar o novo membro
        else:
            st.warning("⚠️ Selecione uma unidade válida.")


def delete_membro(cursor, conn):
    # Buscar membros com nome da unidade
    membros = pd.read_sql("""
                            SELECT membros.ID, membros.Nome, unidades.Nome as Unidade 
                            FROM membros 
                            JOIN unidades ON membros.id_unidade = unidades.ID
                        """, conn)

    if not membros.empty:
        membro_dict = {f"{row['Nome']} ({row['Unidade']})": row["ID"] for _, row in membros.iterrows()}
        membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()))

        membro_id = membro_dict[membro_selecionado]
        membro_info = membros[membros["ID"] == membro_id].iloc[0]
        novo_nome = st.text_input("Nome", membro_info["Nome"])
        unidades = membros['Unidade'].unique()  # Obtém as unidades únicas
        indice_unidade = list(unidades).index(membro_info['Unidade'])  # Encontra o índice correto

        nova_unidade = st.selectbox("Unidade", unidades, index=indice_unidade)
        b1, b2 = st.columns(2)
        if b1.button("Salvar Alterações", key='Alterar'):
            nova_unidade_id = int(pd.read_sql(
                f"SELECT ID FROM unidades WHERE Nome = '{nova_unidade}'", conn
            )['ID'].values[0])
            cursor.execute("UPDATE membros SET Nome = ?, id_unidade = ? WHERE ID = ?",
                           (novo_nome, nova_unidade_id, membro_id))
            conn.commit()
            st.success(f"Membro '{novo_nome}' atualizado com sucesso!")
            membro_atualizado = pd.read_sql(f"SELECT * FROM membros WHERE ID = {membro_id}", conn)
            st.rerun()

        # **Adicionar botão para excluir membro**
        if b2.button("❌ Excluir Membro", key='Deletar'):
            cursor.execute("DELETE FROM membros WHERE ID = ?", (membro_id,))
            conn.commit()
            st.warning(f"Membro '{membro_info['Nome']}' foi excluído!")
            st.rerun()

    else:
        st.warning("Nenhum membro encontrado para editar ou excluir.")

def cadastro_usuarios(c, conn):
    st.subheader("📌 Cadastrar Novo Usuário")

    nome = st.text_input("Nome Completo")
    login = st.text_input("Login")
    senha = st.text_input("Senha", type="password")
    permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho"])

    if st.button("Cadastrar"):
        if nome and login and senha:
            try:
                senha_hash = make_hashes(senha)
                c.execute("INSERT INTO usuarios (nome, login, senha, permissao) VALUES (?, ?, ?, ?)",
                               (nome, login, senha_hash, permissao))
                conn.commit()
                st.success(f"✅ Usuário {nome} cadastrado com sucesso!")
            except sqlite3.IntegrityError:
                st.error("❌ Este login já está cadastrado. Escolha outro.")
        else:
            st.warning("⚠️ Preencha todos os campos!")


def gerenciar_usuario(c, conn):
    st.subheader("📌 Lista de Usuários")

    # Buscar usuários
    usuarios = c.execute("SELECT id, nome, login, permissao FROM usuarios").fetchall()
    df_usuarios = [{"ID": u[0], "Nome": u[1], "Login": u[2], "Permissão": u[3]} for u in usuarios]

    # Exibir tabela de usuários
    if usuarios:
        usuario_selecionado = st.selectbox("Selecione um usuário para editar ou excluir:", df_usuarios,
                                           format_func=lambda x: f"{x['Nome']} ({x['Login']})")

        # **Editar Usuário**
        st.subheader("✏️ Editar Usuário")
        novo_nome = st.text_input("Novo Nome", usuario_selecionado["Nome"])
        novo_login = st.text_input("Novo Login", usuario_selecionado["Login"])
        # Substituir a permissão pelos novos níveis: "equipe", "associado", "conselho"
        nova_permissao = st.selectbox("Nova Permissão", ["equipe", "associado", "conselho"],
                                      index=["equipe", "associado", "conselho"].index(usuario_selecionado["Permissão"]))

        if st.button("Salvar Alterações"):
            c.execute("UPDATE usuarios SET nome = ?, login = ?, permissao = ? WHERE id = ?",
                           (novo_nome, novo_login, nova_permissao, usuario_selecionado["ID"]))
            conn.commit()
            st.success(f"✅ Usuário {novo_nome} atualizado com sucesso!")
            st.rerun()

        # **Excluir Usuário**
        st.subheader("🗑️ Excluir Usuário")
        if st.button("Excluir Usuário"):
            c.execute("DELETE FROM usuarios WHERE id = ?", (usuario_selecionado["ID"],))
            conn.commit()
            st.warning(f"⚠️ Usuário {usuario_selecionado['Nome']} foi excluído!")
            st.rerun()
    else:
        st.info("📌 Nenhum usuário cadastrado.")
