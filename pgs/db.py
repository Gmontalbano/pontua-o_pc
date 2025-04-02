import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from sqlalchemy.sql import select
from sqlalchemy.exc import OperationalError

# **Carregar variáveis de ambiente**
load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# **Criar URL de conexão**
DB_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# **Criar engine global**
engine = create_engine(DB_URL, pool_size=20, max_overflow=10)

# **Criar sessão compartilhada**
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# **Carregar metadados e tabelas**
metadata = MetaData()
metadata.reflect(bind=engine)
tables = {table_name: Table(table_name, metadata, autoload_with=engine) for table_name in metadata.tables.keys()}

print("✅ Conexão estabelecida! Tabelas carregadas:", ", ".join(tables.keys()))

# **Função para obter uma sessão do banco**
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Garante que a conexão é fechada corretamente após o uso

# **Função para obter dados de um usuário**
def get_usuario(login, senha_hash):
    """Obtém informações do usuário e seu membro associado."""
    with Session(engine) as session:
        usuarios_table = tables.get("usuarios")
        membros_table = tables.get("membros")

        if usuarios_table is None or membros_table is None:
            print("❌ Tabelas 'usuarios' ou 'membros' não encontradas.")
            return None

        # **Buscar usuário**
        query_usuarios = select(usuarios_table).where(
            (usuarios_table.c.login == login) & (usuarios_table.c.senha == senha_hash)
        )
        usuario = session.execute(query_usuarios).fetchone()

        if not usuario:
            return None  # Usuário não encontrado

        # **Buscar o membro associado**
        query_membros = select(membros_table).where(membros_table.c.codigo_sgc == usuario.codigo_sgc)
        membro = session.execute(query_membros).fetchone()

        if not membro:
            return None  # Não há correspondência na tabela membros

        # **Retornar os dados do usuário e membro**
        return {
            "id": usuario.id,
            "login": usuario.login,
            "permissao": usuario.permissao,
            "codigo_sgc": usuario.codigo_sgc,
            "nome": membro.nome,
            "id_unidade": membro.id_unidade,
            "cargo": membro.cargo,
        }

# **Função para encerrar a conexão ao finalizar o servidor**
def close_db():
    engine.dispose()
    print("🔌 Conexão com o banco de dados foi fechada.")

