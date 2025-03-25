import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv


def conect_db():
    load_dotenv()
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')

    # Debug: Verificar se as variáveis estão carregadas
    print(f"Usuário: {DB_USER}")
    print(f"Senha recebida: {'✅ DEFINIDA' if DB_PASSWORD else '❌ NÃO DEFINIDA'}")
    print(f"Banco: {DB_NAME}")
    print(f"Host: {DB_HOST}")
    print(f"Porta: {DB_PORT}")

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        return conn, cursor
    except OperationalError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None, None



def get_usuario(username, senha_hash):
    conn, cursor = conect_db()
    # Buscar usuário no banco
    cursor.execute("""
                SELECT membros.nome, usuarios.permissao, usuarios.codigo_sgc
                FROM usuarios 
                JOIN membros ON usuarios.codigo_sgc = membros.codigo_sgc 
                WHERE usuarios.login = (%s) AND usuarios.senha = (%s)
            """, (username, senha_hash))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario
