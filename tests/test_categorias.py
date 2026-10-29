"""Aula 3: categorias e associação com transações."""

import pytest


def test_criar_e_listar_categorias(client):
    r = client.post("/categorias", json={"nome": "  transporte  "})
    assert r.status_code == 201
    assert r.json()["nome"] == "transporte"
    client.post("/categorias", json={"nome": "alimentacao"})
    assert [c["nome"] for c in client.get("/categorias").json()] == ["alimentacao", "transporte"]


@pytest.mark.parametrize("repetido", ["alimentacao", "Alimentacao", " ALIMENTACAO "])
def test_nome_repetido_retorna_422(client, criar_categoria, repetido):
    criar_categoria("alimentacao")
    r = client.post("/categorias", json={"nome": repetido})
    assert r.status_code == 422
    assert r.json() == {"erro": f"nome: categoria '{repetido.strip()}' já existe"}
    assert len(client.get("/categorias").json()) == 1


@pytest.mark.parametrize(
    "nome,mensagem",
    [("", "nome: não pode ser vazia"), ("   ", "nome: não pode ser vazia"), ("123", "nome: não pode conter apenas dígitos")],
)
def test_nome_invalido_retorna_422(client, nome, mensagem):
    r = client.post("/categorias", json={"nome": nome})
    assert r.status_code == 422
    assert r.json() == {"erro": mensagem}


def test_transacao_com_categoria(client, criar_categoria, criar_transacao):
    ali = criar_categoria("alimentacao")
    tra = criar_categoria("transporte")
    t = criar_transacao(categoria_id=ali["id"])
    assert t["categoria_id"] == ali["id"]
    r = client.put(f"/transacoes/{t['id']}", json={**{k: t[k] for k in ("data", "descricao", "valor", "tipo")},
                                                    "categoria_id": tra["id"]})
    assert r.status_code == 200
    assert r.json()["categoria_id"] == tra["id"]


def test_categoria_e_opcional_e_put_sem_ela_remove(client, criar_categoria, criar_transacao):
    ali = criar_categoria("alimentacao")
    assert criar_transacao()["categoria_id"] is None
    t = criar_transacao(categoria_id=ali["id"])
    r = client.put(f"/transacoes/{t['id']}", json={k: t[k] for k in ("data", "descricao", "valor", "tipo")})
    assert r.json()["categoria_id"] is None


@pytest.mark.parametrize(
    "categoria_id,mensagem",
    [
        (999, "categoria_id: categoria 999 não existe"),
        ("1", "categoria_id: deve ser um número inteiro"),
        (True, "categoria_id: deve ser um número inteiro"),
    ],
)
def test_categoria_id_invalido_retorna_422(client, criar_categoria, categoria_id, mensagem):
    criar_categoria("alimentacao")
    corpo = {"data": "2026-08-10", "descricao": "X", "valor": 10, "tipo": "saida", "categoria_id": categoria_id}
    r = client.post("/transacoes", json=corpo)
    assert r.status_code == 422
    assert r.json() == {"erro": mensagem}
