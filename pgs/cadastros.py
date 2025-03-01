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
    codigo_sgc = st.text_input("Código SGC")  # Novo campo para inserir o código SGC

    if st.button("Cadastrar Membro"):
        if unidade_nome and codigo_sgc:
            # Pegar o ID da unidade correspondente ao nome selecionado
            unidade_id = int(unidades[unidades['Nome'] == unidade_nome]['ID'].values[0])

            # Inserir o membro no banco
            c.execute("INSERT INTO membros (Nome, id_unidade, codigo_sgc) VALUES (?, ?, ?)",
                      (nome, unidade_id, codigo_sgc))
            conn.commit()

            st.success(f"Membro '{nome}' cadastrado com sucesso com código SGC {codigo_sgc}!")
            st.rerun()  # Atualiza a tela para mostrar o novo membro
        else:
            st.warning("⚠️ Preencha todos os campos corretamente.")



def delete_membro(cursor, conn):
    # Buscar membros com nome da unidade e codigo_sgc
    membros = pd.read_sql("""
        SELECT membros.ID, membros.Nome, membros.codigo_sgc, unidades.Nome as Unidade 
        FROM membros 
        JOIN unidades ON membros.id_unidade = unidades.ID
    """, conn)

    if not membros.empty:
        membro_dict = {f"{row['Nome']} ({row['Unidade']})": row["ID"] for _, row in membros.iterrows()}
        membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()))

        membro_id = membro_dict[membro_selecionado]
        membro_info = membros[membros["ID"] == membro_id].iloc[0]

        # Campos de edição
        novo_nome = st.text_input("Nome", membro_info["Nome"])
        novo_codigo_sgc = st.text_input("Código SGC", membro_info["codigo_sgc"])  # Adicionado para edição do código
        unidades = membros['Unidade'].unique()
        indice_unidade = list(unidades).index(membro_info['Unidade'])

        nova_unidade = st.selectbox("Unidade", unidades, index=indice_unidade)

        b1, b2 = st.columns(2)

        # **Salvar Alterações**
        if b1.button("💾 Salvar Alterações", key='Alterar'):
            nova_unidade_id = int(pd.read_sql(
                f"SELECT ID FROM unidades WHERE Nome = ?", conn, params=[nova_unidade]
            )['ID'].values[0])

            cursor.execute("UPDATE membros SET Nome = ?, codigo_sgc = ?, id_unidade = ? WHERE ID = ?",
                           (novo_nome, novo_codigo_sgc, nova_unidade_id, membro_id))
            conn.commit()
            st.success(f"✅ Membro '{novo_nome}' atualizado com sucesso!")
            st.rerun()

        # **Excluir Membro**
        if b2.button("❌ Excluir Membro", key='Deletar'):
            cursor.execute("DELETE FROM membros WHERE ID = ?", (membro_id,))
            conn.commit()
            st.warning(f"⚠️ Membro '{membro_info['Nome']}' foi excluído!")
            st.rerun()

    else:
        st.warning("📌 Nenhum membro encontrado para editar ou excluir.")


def gerenciar_usuarios(c, conn):
    st.subheader("📌 Gerenciar Usuários")

    # Buscar membros disponíveis (Nome e codigo_sgc)
    membros = pd.read_sql("SELECT Nome, codigo_sgc FROM membros", conn)

    if membros.empty:
        st.warning("⚠️ Nenhum membro encontrado. Cadastre um membro antes de criar um usuário.")
        return  # Interrompe a execução se não houver membros

    # Criar lista formatada para exibir nome + código SGC
    membros["Display"] = membros["codigo_sgc"] + " - " + membros["Nome"]

    # Seleção do membro pelo código SGC
    membro_selecionado = st.selectbox("Selecione o Membro", membros["Display"], index=0)

    # Obter o código SGC real do membro selecionado
    codigo_sgc = membros.loc[membros["Display"] == membro_selecionado, "codigo_sgc"].values[0]

    # Verificar se o usuário já existe na tabela `usuarios`
    usuario_existente = pd.read_sql("SELECT id, login, permissao FROM usuarios WHERE codigo_sgc = ?", conn, params=[codigo_sgc])

    col1, col2 = st.columns(2)  # Criar duas colunas para organizar os botões

    if not usuario_existente.empty:
        st.warning("⚠️ Este membro já tem um usuário cadastrado. Você pode editar ou excluir abaixo.")

        usuario_id = usuario_existente["id"].values[0]
        login = st.text_input("Login", usuario_existente["login"].values[0])
        senha = st.text_input("Senha (Deixe em branco para manter a atual)", type="password")
        permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho"],
                                 index=["equipe", "associado", "conselho"].index(usuario_existente["permissao"].values[0]))

        if col1.button("💾 Salvar Alterações", key=f"salvar_{usuario_id}"):
            if senha:  # Se uma nova senha foi inserida, atualiza com hash
                senha_hash = make_hashes(senha)
                c.execute("UPDATE usuarios SET login = ?, senha = ?, permissao = ? WHERE id = ?",
                          (login, senha_hash, permissao, usuario_id))
            else:  # Mantém a senha atual
                c.execute("UPDATE usuarios SET login = ?, permissao = ? WHERE id = ?",
                          (login, permissao, usuario_id))

            conn.commit()
            st.success(f"✅ Usuário atualizado com sucesso!")
            st.rerun()

        if col2.button("❌ Excluir Usuário", key=f"excluir_{usuario_id}"):
            c.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
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
                    c.execute("INSERT INTO usuarios (codigo_sgc, login, senha, permissao) VALUES (?, ?, ?, ?)",
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
