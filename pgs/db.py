import psycopg2
from psycopg2 import OperationalError
import os
import sys
from configparser import ConfigParser



def conect_db():
    site_module_path = os.path.dirname(sys.executable)
    # Verifica se o caminho contém 'Scripts' (Windows) ou 'bin' (Linux/Mac)
    if 'Scripts' in site_module_path:
        venv_name = os.path.basename(os.path.dirname(site_module_path))
    elif 'bin' in site_module_path:
        venv_name = os.path.basename(os.path.dirname(os.path.dirname(site_module_path)))
    else:
        venv_name = None  # Não foi possível determinar o nome do venv
        print('No virtual environment folder found. Create a virtual environment.')
    VENV_FOLDER = venv_name

    key = f"./{VENV_FOLDER}/keys.cfg"

    parser = ConfigParser()
    _ = parser.read(key)
    db_url = parser.get('postgres', 'db_url')

    try:
        conn = psycopg2.connect(db_url)
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
