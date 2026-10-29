"""Aula 4: saldo total e resumo mensal."""

import pytest


def test_saldo_banco_vazio(client):
    r = client.get("/saldo")
    assert r.status_code == 200
    assert r.json() == {"entradas": 0, "saidas": 0, "saldo": 0}


@pytest.fixture
def lancamentos(criar_categoria, criar_transacao):
    ali = criar_categoria("alimentacao")
    tra = criar_categoria("transporte")
    criar_transacao(data="2026-07-31", valor=1000, tipo="entrada")
    criar_transacao(data="2026-08-01", valor=3000.10, tipo="entrada")
    criar_transacao(data="2026-08-05", valor=0.20, tipo="entrada", categoria_id=ali["id"])  # entrada: fora de por_categoria
    criar_transacao(data="2026-08-31", valor=0.10, categoria_id=ali["id"])
    criar_transacao(data="2026-08-15", valor=0.20, categoria_id=ali["id"])
    criar_transacao(data="2026-08-10", valor=150, categoria_id=tra["id"])
    criar_transacao(data="2026-08-20", valor=49.99)
    criar_transacao(data="2026-09-01", valor=5000, categoria_id=tra["id"])


def test_saldo_considera_todas_as_transacoes(client, lancamentos):
    assert client.get("/saldo").json() == {"entradas": 4000.30, "saidas": 5200.29, "saldo": -1199.99}


def test_resumo_do_mes(client, lancamentos):
    r = client.get("/resumo", params={"mes": "2026-08"})
    assert r.status_code == 200
    assert r.json() == {
        "mes": "2026-08",
        "entradas": 3000.30,
        "saidas": 200.29,
        "saldo": 2800.01,
        "por_categoria": [
            {"categoria": "transporte", "total": 150.0},
            {"categoria": None, "total": 49.99},
            {"categoria": "alimentacao", "total": 0.30},
        ],
    }


def test_por_categoria_soma_igual_a_saidas(client, lancamentos):
    j = client.get("/resumo", params={"mes": "2026-08"}).json()
    assert round(sum(c["total"] for c in j["por_categoria"]), 2) == j["saidas"]


def test_resumo_mes_sem_transacoes(client, lancamentos):
    r = client.get("/resumo", params={"mes": "2026-01"})
    assert r.status_code == 200
    assert r.json() == {"mes": "2026-01", "entradas": 0, "saidas": 0, "saldo": 0, "por_categoria": []}


@pytest.mark.parametrize("mes", ["2026-13", "2026-00", "2026-8", "08-2026", "2026-08-01", "abc", "", "2026-08\n"])
def test_resumo_mes_malformado_retorna_422(client, mes):
    r = client.get("/resumo", params={"mes": mes})
    assert r.status_code == 422
    assert r.json() == {"erro": "mes: deve ser um mês válido no formato YYYY-MM"}


def test_resumo_sem_mes_retorna_422(client):
    r = client.get("/resumo")
    assert r.status_code == 422
    assert r.json() == {"erro": "mes: campo obrigatório"}
