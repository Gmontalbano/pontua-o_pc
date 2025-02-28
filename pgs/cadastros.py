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


def cadastro_unidade(c, conn):
    st.subheader("Cadastro de Unidade")
    nome = st.text_input("Nome da Unidade")
    if st.button("Cadastrar Unidade"):
        c.execute("INSERT INTO unidades (Nome) VALUES (?)", (nome,))
        conn.commit()
        st.success("Unidade cadastrada com sucesso!")


def cadastro_membro(c, conn):
    st.subheader("Cadastro de Membro")
    unidades = pd.read_sql("SELECT Nome FROM unidades", conn)
    nome = st.text_input("Nome do Membro")
    unidade = st.selectbox("Unidade", unidades['Nome'] if not unidades.empty else [])
    if st.button("Cadastrar Membro"):
        c.execute("INSERT INTO membros (Nome, Unidade) VALUES (?, ?)", (nome, unidade))
        conn.commit()
        st.success("Membro cadastrado com sucesso!")


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
