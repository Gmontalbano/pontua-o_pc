import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import insert
from sqlalchemy.sql import select, update, delete
from utils.hashes import make_hashes
import pandas as pd
from pgs.db import engine, get_db, tables
from sqlalchemy.exc import IntegrityError


def cadastro_reuniao():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    reunioes = tables.get("reunioes")

    if reunioes is None:  # Alterado para evitar o erro de booleano
        st.error("❌ A tabela 'reunioes' não foi encontrada no banco de dados.")
        return

    st.subheader("Cadastro de Reunião")
    nome = st.text_input("Nome da Reunião")
    data = st.date_input("Data", value=datetime.today())

    if st.button("Cadastrar Reunião"):
        try:
            with Session(engine) as session:
                stmt = insert(reunioes).values(nome=nome, data=data)
                session.execute(stmt)
                session.commit()

            st.success("✅ Reunião cadastrada com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao cadastrar reunião: {e}")



def delete_reuniao():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    reunioes = tables.get("reunioes")

    if reunioes is None:  # Alterado para evitar o erro de booleano
        st.error("❌ A tabela 'reunioes' não foi encontrada no banco de dados.")
        return

    st.subheader("📅 Gerenciar Reuniões")

    # Buscar reuniões existentes
    try:
        with Session(engine) as session:
            stmt = select(reunioes.c.id, reunioes.c.nome, reunioes.c.data)
            result = session.execute(stmt).fetchall()

        if result:
            reuniao_selecionada = st.selectbox(
                "Selecione a reunião:",
                result,
                format_func=lambda x: f"{x[1]} ({x[2]}) - ID {x[0]}"
            )

            # Campos para edição
            novo_nome = st.text_input("Novo Nome", reuniao_selecionada[1])
            nova_data = st.date_input("Nova Data", pd.to_datetime(reuniao_selecionada[2]))

            col1, col2 = st.columns(2)

            # Botão para salvar alterações
            if col1.button("💾 Salvar Alterações"):
                try:
                    with Session(engine) as session:
                        stmt = (
                            update(reunioes)
                            .where(reunioes.c.id == reuniao_selecionada[0])
                            .values(nome=novo_nome, data=nova_data)
                        )
                        session.execute(stmt)
                        session.commit()

                    st.success(f"✅ Reunião '{novo_nome}' atualizada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar reunião: {e}")

            # Botão para excluir reunião
            if col2.button("❌ Excluir Reunião"):
                try:
                    with Session(engine) as session:
                        stmt = delete(reunioes).where(reunioes.c.id == reuniao_selecionada[0])
                        session.execute(stmt)
                        session.commit()

                    st.warning(f"⚠️ Reunião '{reuniao_selecionada[1]}' foi excluída!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao excluir reunião: {e}")

        else:
            st.info("📌 Nenhuma reunião encontrada.")

    except Exception as e:
        st.error(f"❌ Erro ao buscar reuniões: {e}")


def cadastro_unidade():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    unidades = tables.get("unidades")

    if unidades is None:  # Alterado para evitar o erro de booleano
        st.error("❌ A tabela 'reunioes' não foi encontrada no banco de dados.")
        return

    st.subheader("Cadastro de Unidade")
    nome = st.text_input("Nome da Unidade")

    if st.button("Cadastrar Unidade"):
        if nome.strip() == "":
            st.warning("⚠️ O nome da unidade não pode estar vazio.")
            return

        try:
            with Session(engine) as session:
                stmt = insert(unidades).values(nome=nome)
                session.execute(stmt)
                session.commit()

            st.success("✅ Unidade cadastrada com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao cadastrar unidade: {e}")


def cadastro_membro():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    unidades = tables.get("unidades")

    if membros is None or unidades is None:
        st.error("❌ As tabelas 'membros' ou 'unidades' não foram encontradas no banco de dados.")
        return

    st.subheader("Cadastro de Membro")

    # Buscar unidades
    with Session(engine) as session:
        result = session.execute(select(unidades.c.id, unidades.c.nome)).fetchall()

    unidade_opcoes = {row[1]: row[0] for row in result} if result else {}

    nome = st.text_input("Nome do Membro")
    unidade_nome = st.selectbox("Unidade", list(unidade_opcoes.keys()), key='unidade_nome')
    codigo_sgc = st.text_input("Código SGC")  # Campo para inserir o código SGC
    cargo = st.selectbox("Cargo", ['Conselheiro', 'Desbravador', 'Diretor Associado',
                                   'Secretário', 'Instrutor', 'Apoio', 'Tesoureiro'], key="Cargo")

    if st.button("Cadastrar Membro"):
        if nome.strip() and unidade_nome and codigo_sgc.strip():
            unidade_id = unidade_opcoes[unidade_nome]

            try:
                with Session(engine) as session:
                    stmt = insert(membros).values(
                        nome=nome, id_unidade=unidade_id, codigo_sgc=codigo_sgc, cargo=cargo
                    )
                    session.execute(stmt)
                    session.commit()

                st.success(f"✅ Membro '{nome}' cadastrado com sucesso com código SGC {codigo_sgc}!")
                st.rerun()  # Atualiza a tela para mostrar o novo membro
            except Exception as e:
                st.error(f"❌ Erro ao cadastrar membro: {e}")
        else:
            st.warning("⚠️ Preencha todos os campos corretamente.")


def delete_membro():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    unidades = tables.get("unidades")

    if membros is None or unidades is None:
        st.error("❌ As tabelas 'membros' ou 'unidades' não foram encontradas no banco de dados.")
        return

    # Buscar membros com nome da unidade e codigo_sgc
    with Session(engine) as session:
        result = session.execute(
            select(membros.c.id, membros.c.nome, membros.c.codigo_sgc, membros.c.cargo, unidades.c.nome.label("unidade"))
            .join(unidades, membros.c.id_unidade == unidades.c.id)
        ).fetchall()

    if result:
        df_membros = pd.DataFrame(result, columns=["id", "nome", "codigo_sgc", "cargo", "unidade"])
        membro_dict = {f"{row['nome']} ({row['unidade']})": row["id"] for _, row in df_membros.iterrows()}
        membro_selecionado = st.selectbox("Selecione o membro:", list(membro_dict.keys()))

        membro_id = membro_dict[membro_selecionado]
        membro_info = df_membros[df_membros["id"] == membro_id].iloc[0]

        # Campos de edição
        novo_nome = st.text_input("Nome", membro_info["nome"])
        novo_codigo_sgc = st.text_input("Código SGC", membro_info["codigo_sgc"])

        # Se `cargo` for None, define como "Selecione um cargo"
        cargo_atual = membro_info["cargo"] if membro_info["cargo"] is not None else "Selecione um cargo"
        cargos_disponiveis = [
            "Selecione um cargo", "Conselheiro", "Desbravador", "Diretor Associado",
            "Secretário", "Instrutor", "Apoio", "Tesoureiro"
        ]
        novo_cargo = st.selectbox("Cargo", cargos_disponiveis,
                                  index=cargos_disponiveis.index(cargo_atual) if cargo_atual in cargos_disponiveis else 0)

        unidades_disponiveis = df_membros["unidade"].unique().tolist()
        nova_unidade = st.selectbox("Unidade", unidades_disponiveis, index=unidades_disponiveis.index(membro_info["unidade"]))

        col1, col2 = st.columns(2)

        # **Salvar Alterações**
        if col1.button("💾 Salvar Alterações", key='Alterar'):
            with Session(engine) as session:
                nova_unidade_id = session.execute(
                    select(unidades.c.id).where(unidades.c.nome == nova_unidade)
                ).scalar()

                stmt = update(membros).where(membros.c.id == membro_id).values(
                    nome=novo_nome, codigo_sgc=novo_codigo_sgc, id_unidade=nova_unidade_id, cargo=novo_cargo
                )
                session.execute(stmt)
                session.commit()

            st.success(f"✅ Membro '{novo_nome}' atualizado com sucesso!")
            st.rerun()

        # **Excluir Membro**
        if col2.button("❌ Excluir Membro", key='Deletar'):
            with Session(engine) as session:
                stmt = delete(membros).where(membros.c.id == membro_id)
                session.execute(stmt)
                session.commit()

            st.warning(f"⚠️ Membro '{membro_info['nome']}' foi excluído!")
            st.rerun()

    else:
        st.warning("📌 Nenhum membro encontrado para editar ou excluir.")


def gerenciar_usuarios():

    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    membros = tables.get("membros")
    usuarios = tables.get("usuarios")

    if membros is None or usuarios is None:
        st.error("❌ As tabelas 'membros' ou 'usuarios' não foram encontradas.")
        return

    # Buscar membros disponíveis
    with Session(engine) as session:
        result = session.execute(select(membros.c.nome, membros.c.codigo_sgc)).fetchall()

    if not result:
        st.warning("⚠️ Nenhum membro encontrado. Cadastre um membro antes de criar um usuário.")
        return

    df_membros = pd.DataFrame(result, columns=["nome", "codigo_sgc"])
    df_membros["Display"] = df_membros["codigo_sgc"] + " - " + df_membros["nome"]

    # Seleção do membro pelo código SGC
    membro_selecionado = st.selectbox("Selecione o Membro", df_membros["Display"])
    codigo_sgc = df_membros.loc[df_membros["Display"] == membro_selecionado, "codigo_sgc"].values[0]

    # Buscar usuário existente
    with Session(engine) as session:
        usuario_existente = session.execute(
            select(usuarios.c.id, usuarios.c.login, usuarios.c.permissao)
            .where(usuarios.c.codigo_sgc == codigo_sgc)
        ).fetchone()

    col1, col2 = st.columns(2)

    if usuario_existente:
        st.warning("⚠️ Este membro já tem um usuário cadastrado. Você pode editar ou excluir abaixo.")

        usuario_id, login_atual, permissao_atual = usuario_existente

        login = st.text_input("Login", login_atual)
        senha = st.text_input("Senha (Deixe em branco para manter a atual)", type="password")
        permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho", "admin"],
                                 index=["equipe", "associado", "conselho", "admin"].index(permissao_atual))

        if col1.button("💾 Salvar Alterações", key=f"salvar_{usuario_id}"):
            with Session(engine) as session:
                stmt = update(usuarios).where(usuarios.c.id == usuario_id).values(
                    login=login, permissao=permissao
                )
                session.execute(stmt)

                if senha:
                    senha_hash = make_hashes(senha)
                    session.execute(update(usuarios).where(usuarios.c.id == usuario_id).values(senha=senha_hash))

                session.commit()
                st.success(f"✅ Usuário atualizado com sucesso!")
                st.rerun()

        if col2.button("❌ Excluir Usuário", key=f"excluir_{usuario_id}"):
            with Session(engine) as session:
                session.execute(delete(usuarios).where(usuarios.c.id == usuario_id))
                session.commit()
            st.warning(f"⚠️ Usuário foi excluído!")
            st.rerun()

    else:  # Cadastro de novo usuário
        st.subheader("✅ Cadastrar Novo Usuário")
        login = st.text_input("Login")
        senha = st.text_input("Senha", type="password")
        permissao = st.selectbox("Permissão", ["equipe", "associado", "conselho"])

        if st.button("Cadastrar Usuário", key="cadastrar_usuario"):
            if codigo_sgc and login and senha:
                try:
                    senha_hash = make_hashes(senha)
                    with Session(engine) as session:
                        session.execute(insert(usuarios).values(
                            codigo_sgc=codigo_sgc, login=login, senha=senha_hash, permissao=permissao
                        ))
                        session.commit()
                    st.success(f"✅ Usuário cadastrado com sucesso para o membro {membro_selecionado}!")
                    st.rerun()

                except IntegrityError:
                    st.error("❌ Este login já está cadastrado. Escolha outro.")

                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")

            else:
                st.warning("⚠️ Preencha todos os campos!")


def cadastro_especialidade():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    especialidades = tables.get("especialidades")

    with st.expander("➕ Nova especialidade"):
        codigo_esp = st.text_input('Código da especialidade', 'XX-000')
        nome_esp = st.text_input('Nome da especialidade')

        if st.button("✅ Cadastrar Especialidade"):
            if codigo_esp and nome_esp:
                with Session(engine) as session:
                    # Verificar se o código já existe
                    existe = session.execute(
                        select(especialidades.c.codigo).where(especialidades.c.codigo == codigo_esp)
                    ).fetchone()

                    if existe:
                        st.warning(f"⚠️ Já existe uma especialidade com o código **{codigo_esp}**!")
                    else:
                        stmt = insert(especialidades).values(codigo=codigo_esp, nome=nome_esp)
                        session.execute(stmt)
                        session.commit()
                        st.success("✅ Especialidade cadastrada com sucesso!")
                        st.rerun()
            else:
                st.warning("⚠️ Preencha todos os campos.")

    with st.expander("📂 Upload de Arquivo (.xlsx)"):
        arquivo = st.file_uploader("Escolha um arquivo Excel", type=["xlsx"])

        if arquivo is not None:
            df = pd.read_excel(arquivo)

            if not {'codigo', 'nome'}.issubset(df.columns):
                st.error("❌ O arquivo deve ter as colunas: 'codigo' e 'nome'.")
                return

            st.dataframe(df)  # Mostrar prévia do arquivo

            with Session(engine) as session:
                # Obter todos os códigos já cadastrados no banco
                codigos_existentes = set(row[0] for row in session.execute(select(especialidades.c.codigo)).fetchall())

            # Separar os novos e os duplicados
            df_novos = df[~df['codigo'].isin(codigos_existentes)]
            df_duplicados = df[df['codigo'].isin(codigos_existentes)]
            atualizar = False
            if not df_novos.empty:
                st.write(f"✅ {len(df_novos)} novas especialidades encontradas para cadastrar.")

            if not df_duplicados.empty:
                st.warning(f"⚠️ {len(df_duplicados)} especialidades já existem no banco.")
                atualizar = st.checkbox("🔄 Atualizar especialidades existentes")

            if st.button("📥 Salvar no Banco"):
                with Session(engine) as session:
                    if not df_novos.empty:
                        session.execute(insert(especialidades), df_novos.to_dict(orient="records"))

                    if atualizar and not df_duplicados.empty:
                        for _, row in df_duplicados.iterrows():
                            session.execute(
                                update(especialidades)
                                .where(especialidades.c.codigo == row['codigo'])
                                .values(nome=row['nome'])
                            )

                    session.commit()

                st.success("✅ Especialidades cadastradas/atualizadas com sucesso!")
                st.rerun()


def cadastro_classe():
    if not engine:
        st.error("❌ Erro ao conectar ao banco de dados.")
        return

    classe = tables.get("classe")

    with st.expander("➕ Nova classe"):
        codigo_cl = st.text_input('Código da classe')
        nome_cl = st.text_input('Nome da classe')

        if st.button("✅ Cadastrar Classe"):
            if codigo_cl and nome_cl:
                with Session(engine) as session:
                    # Verificar se o código já existe
                    existe = session.execute(
                        select(classe.c.codigo).where(classe.c.codigo == codigo_cl)
                    ).fetchone()

                    if existe:
                        st.warning(f"⚠️ Já existe uma classe com o código **{codigo_cl}**!")
                    else:
                        stmt = insert(classe).values(codigo=codigo_cl, nome=nome_cl)
                        session.execute(stmt)
                        session.commit()
                        st.success("✅ Classe cadastrada com sucesso!")
                        st.rerun()
            else:
                st.warning("⚠️ Preencha todos os campos.")
