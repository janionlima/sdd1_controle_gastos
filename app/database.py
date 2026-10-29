"""Acesso a dados: conexão SQLite e criação do schema."""

import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv(
    "GASTOS_DB_PATH",
    str(Path(__file__).resolve().parent.parent / "gastos.db"),
)

# Cada tabela entra aqui com CREATE TABLE IF NOT EXISTS.
SCHEMA = """
CREATE TABLE IF NOT EXISTS transacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,            -- ISO YYYY-MM-DD
    descricao TEXT NOT NULL,
    valor_centavos INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria o arquivo do banco e as tabelas, se ainda não existirem."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Converte uma linha de `transacao` para o formato da API (valor em reais)."""
    return {
        "id": row["id"],
        "data": row["data"],
        "descricao": row["descricao"],
        "valor": row["valor_centavos"] / 100,
        "tipo": row["tipo"],
    }


def _para_centavos(valor: float) -> int:
    return round(valor * 100)


def criar_transacao(data: str, descricao: str, valor: float, tipo: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO transacao (data, descricao, valor_centavos, tipo) VALUES (?, ?, ?, ?)",
            (data, descricao, _para_centavos(valor), tipo),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM transacao WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def buscar_transacao(id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM transacao WHERE id = ?", (id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def atualizar_transacao(id: int, data: str, descricao: str, valor: float, tipo: str) -> dict | None:
    """Substitui todos os campos da transação; retorna None se o id não existir."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE transacao SET data = ?, descricao = ?, valor_centavos = ?, tipo = ? WHERE id = ?",
            (data, descricao, _para_centavos(valor), tipo, id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        row = conn.execute("SELECT * FROM transacao WHERE id = ?", (id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def excluir_transacao(id: int) -> bool:
    """Remove a transação; retorna False se o id não existir."""
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM transacao WHERE id = ?", (id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def listar_transacoes() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM transacao ORDER BY data DESC, id DESC").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()
