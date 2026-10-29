"""Acesso a dados: conexão SQLite e criação do schema."""

import math
import os
import sqlite3
from pathlib import Path

from app.models import FiltrosTransacao, so_digitos

DB_PATH = os.getenv(
    "GASTOS_DB_PATH",
    str(Path(__file__).resolve().parent.parent / "gastos.db"),
)

# Cada tabela entra aqui com CREATE TABLE IF NOT EXISTS.
SCHEMA = """
CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS transacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,            -- ISO YYYY-MM-DD
    descricao TEXT NOT NULL,
    valor_centavos INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    categoria_id INTEGER REFERENCES categoria(id)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Cria o arquivo do banco e as tabelas, se ainda não existirem."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        # Migração (Aula 3): bancos criados antes das categorias não têm a coluna.
        colunas = {r["name"] for r in conn.execute("PRAGMA table_info(transacao)")}
        if "categoria_id" not in colunas:
            conn.execute("ALTER TABLE transacao ADD COLUMN categoria_id INTEGER REFERENCES categoria(id)")
            conn.commit()
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
        "categoria_id": row["categoria_id"],
    }


def _para_centavos(valor: float) -> int:
    return round(valor * 100)


def _centavos_teto(valor: float) -> int:
    """Menor centavo >= valor (round(..., 6) descarta o ruído de ponto flutuante, ex.: 0.3*100)."""
    return math.ceil(round(valor * 100, 6))


def _centavos_piso(valor: float) -> int:
    """Maior centavo <= valor."""
    return math.floor(round(valor * 100, 6))


def _id_existe_no_sqlite(id: int) -> bool:
    """Ids fora do INTEGER de 64 bits não podem existir (e o sqlite3 levantaria OverflowError)."""
    return -(2**63) <= id < 2**63


def criar_transacao(data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO transacao (data, descricao, valor_centavos, tipo, categoria_id) VALUES (?, ?, ?, ?, ?)",
            (data, descricao, _para_centavos(valor), tipo, categoria_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM transacao WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def buscar_transacao(id: int) -> dict | None:
    if not _id_existe_no_sqlite(id):
        return None
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM transacao WHERE id = ?", (id,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def atualizar_transacao(
    id: int, data: str, descricao: str, valor: float, tipo: str, categoria_id: int | None
) -> dict | None:
    """Substitui todos os campos da transação; retorna None se o id não existir."""
    if not _id_existe_no_sqlite(id):
        return None
    conn = get_connection()
    try:
        cur = conn.execute(
            "UPDATE transacao SET data = ?, descricao = ?, valor_centavos = ?, tipo = ?, categoria_id = ?"
            " WHERE id = ?",
            (data, descricao, _para_centavos(valor), tipo, categoria_id, id),
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
    if not _id_existe_no_sqlite(id):
        return False
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM transacao WHERE id = ?", (id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def listar_transacoes(filtros: FiltrosTransacao | None = None) -> list[dict]:
    """Lista transações aplicando os filtros preenchidos (E lógico, limites inclusivos).

    `categoria` só com dígitos ASCII é id, senão é nome (sem diferenciar maiúsculas). Os limites de
    valor arredondam para dentro da faixa (teto/piso em centavos). A query concatena apenas trechos
    fixos; todo valor vindo do usuário vai por parâmetro vinculado (`?`).
    """
    condicoes: list[str] = []
    params: list = []
    if filtros is not None:
        if filtros.categoria is not None:
            if so_digitos(filtros.categoria):
                if not _id_existe_no_sqlite(int(filtros.categoria)):
                    return []  # id grande demais: nenhuma categoria pode tê-lo
                condicoes.append("categoria_id = ?")
                params.append(int(filtros.categoria))
            else:
                condicoes.append("categoria_id IN (SELECT id FROM categoria WHERE nome = ?)")
                params.append(filtros.categoria)
        if filtros.data_inicio is not None:
            condicoes.append("data >= ?")
            params.append(filtros.data_inicio.isoformat())
        if filtros.data_fim is not None:
            condicoes.append("data <= ?")
            params.append(filtros.data_fim.isoformat())
        if filtros.valor_min is not None:
            condicoes.append("valor_centavos >= ?")
            params.append(_centavos_teto(filtros.valor_min))
        if filtros.valor_max is not None:
            condicoes.append("valor_centavos <= ?")
            params.append(_centavos_piso(filtros.valor_max))

    sql = "SELECT * FROM transacao"
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    sql += " ORDER BY data DESC, id DESC"

    conn = get_connection()
    try:
        return [_row_to_dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def criar_categoria(nome: str) -> dict | None:
    """Cria a categoria; retorna None se já existir uma com esse nome."""
    conn = get_connection()
    try:
        try:
            cur = conn.execute("INSERT INTO categoria (nome) VALUES (?)", (nome,))
        except sqlite3.IntegrityError:
            return None
        conn.commit()
        return {"id": cur.lastrowid, "nome": nome}
    finally:
        conn.close()


def buscar_categoria(id: int) -> dict | None:
    if not _id_existe_no_sqlite(id):
        return None
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, nome FROM categoria WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def listar_categorias() -> list[dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute("SELECT id, nome FROM categoria ORDER BY nome").fetchall()]
    finally:
        conn.close()


# Agregações: somadas em centavos (inteiros) no SQL e convertidas para reais só no fim.
_SQL_TOTAIS = """
SELECT COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor_centavos END), 0) AS entradas,
       COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor_centavos END), 0) AS saidas
FROM transacao
"""


def _totais(conn: sqlite3.Connection, where: str = "", params: tuple = ()) -> dict:
    row = conn.execute(_SQL_TOTAIS + where, params).fetchone()
    return {
        "entradas": row["entradas"] / 100,
        "saidas": row["saidas"] / 100,
        "saldo": (row["entradas"] - row["saidas"]) / 100,
    }


def calcular_saldo() -> dict:
    conn = get_connection()
    try:
        return _totais(conn)
    finally:
        conn.close()


def calcular_resumo(mes: str) -> dict:
    """Totais do mês (YYYY-MM) e gastos (saídas) por categoria; sem categoria → `categoria: None`."""
    conn = get_connection()
    try:
        totais = _totais(conn, "WHERE substr(data, 1, 7) = ?", (mes,))
        rows = conn.execute(
            """
            SELECT c.nome AS categoria, SUM(t.valor_centavos) AS total
            FROM transacao t LEFT JOIN categoria c ON c.id = t.categoria_id
            WHERE t.tipo = 'saida' AND substr(t.data, 1, 7) = ?
            GROUP BY t.categoria_id
            ORDER BY total DESC, categoria
            """,
            (mes,),
        ).fetchall()
        por_categoria = [{"categoria": r["categoria"], "total": r["total"] / 100} for r in rows]
        return {"mes": mes, **totais, "por_categoria": por_categoria}
    finally:
        conn.close()
