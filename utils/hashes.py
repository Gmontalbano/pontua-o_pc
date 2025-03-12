import hashlib
import sqlite3


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def obter_permissao(username, password):
    """Obtém a permissão de um usuário após validar a senha."""
    try:
        with sqlite3.connect('registro_chamada.db') as conn:
            cursor = conn.cursor()

        # Query para validar o usuário e senha
        query = "SELECT nome, permissao FROM usuarios WHERE login = %s AND senha = %s"
        cursor.execute(query, (username, password))
        resultado = cursor.fetchone()
        p = resultado[1]
        n = resultado[0]
        if resultado:
            return p, n  # Retorna a permissão
        else:
            return None, None
    except Exception as e:
        return None, None