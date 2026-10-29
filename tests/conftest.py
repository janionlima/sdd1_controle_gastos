"""Fixtures dos testes: cada teste roda com um banco SQLite novo e vazio, nunca o `gastos.db`."""

import os
import tempfile

# Garantia extra: definido antes de importar o app, para que nada aponte para o banco de produção.
os.environ["GASTOS_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "nao-usar.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.database  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app.database, "DB_PATH", str(tmp_path / "teste.db"))
    with TestClient(fastapi_app) as c:  # o `with` roda o lifespan (init_db)
        yield c


@pytest.fixture
def criar_transacao(client):
    """Cria uma transação válida, sobrescrevendo só os campos informados; retorna o JSON criado."""

    def _criar(**campos):
        payload = {"data": "2026-08-10", "descricao": "Teste", "valor": 10.0, "tipo": "saida", **campos}
        r = client.post("/transacoes", json=payload)
        assert r.status_code == 201, r.json()
        return r.json()

    return _criar


@pytest.fixture
def criar_categoria(client):
    def _criar(nome):
        r = client.post("/categorias", json={"nome": nome})
        assert r.status_code == 201, r.json()
        return r.json()

    return _criar


def ids(resposta) -> list[int]:
    return [t["id"] for t in resposta.json()]
