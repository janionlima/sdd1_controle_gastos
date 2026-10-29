"""Sobe o servidor com configuração vinda do ambiente: `python -m app`.

Variáveis: HOST (padrão 127.0.0.1; use 0.0.0.0 em deploy), PORT (padrão 8000) e
GASTOS_DB_PATH (caminho do SQLite, lido em app/database.py).
"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
