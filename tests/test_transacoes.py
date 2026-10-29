"""Aulas 1–2: CRUD de transações e validação."""

import pytest

from tests.conftest import ids

VALIDA = {"data": "2026-08-10", "descricao": "Mercado", "valor": 50.5, "tipo": "saida"}


def test_criar_retorna_201_com_id(client):
    r = client.post("/transacoes", json={**VALIDA, "descricao": "  Mercado  "})
    assert r.status_code == 201
    assert r.json() == {**VALIDA, "categoria_id": None, "id": r.json()["id"]}  # descricao sem espaços


def test_listar_vazio(client):
    r = client.get("/transacoes")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_ordena_por_data_desc_e_id_desc(client, criar_transacao):
    a = criar_transacao(data="2026-08-01")
    b = criar_transacao(data="2026-08-20")
    c = criar_transacao(data="2026-08-01")
    assert ids(client.get("/transacoes")) == [b["id"], c["id"], a["id"]]


@pytest.mark.parametrize(
    "enviado,gravado",
    [(0.1, 0.1), (0.01, 0.01), (10.006, 10.01), (10.004, 10.0), (1_000_000_000, 1_000_000_000.0)],
)
def test_valor_guarda_duas_casas(client, enviado, gravado):
    r = client.post("/transacoes", json={**VALIDA, "valor": enviado})
    assert r.status_code == 201
    assert r.json()["valor"] == gravado
    assert client.get("/transacoes").status_code == 200


def test_valor_subcentavo_nao_e_gravado(client):
    """Regressão: 0.001 era gravado como 0 centavos e quebrava toda listagem seguinte (500)."""
    assert client.post("/transacoes", json={**VALIDA, "valor": 0.001}).status_code == 422
    r = client.get("/transacoes")
    assert r.status_code == 200
    assert r.json() == []


def test_buscar_por_id(client, criar_transacao):
    t = criar_transacao()
    r = client.get(f"/transacoes/{t['id']}")
    assert r.status_code == 200
    assert r.json() == t


def test_editar_reflete_na_listagem(client, criar_transacao):
    t = criar_transacao()
    novo = {"data": "2026-09-15", "descricao": "Salário", "valor": 3200, "tipo": "entrada"}
    r = client.put(f"/transacoes/{t['id']}", json=novo)
    assert r.status_code == 200
    esperado = {**novo, "valor": 3200.0, "categoria_id": None, "id": t["id"]}
    assert r.json() == esperado
    assert client.get("/transacoes").json() == [esperado]


def test_excluir_e_buscar_depois_retorna_404(client, criar_transacao):
    t = criar_transacao()
    r = client.delete(f"/transacoes/{t['id']}")
    assert r.status_code == 204
    assert r.content == b""
    r = client.get(f"/transacoes/{t['id']}")
    assert r.status_code == 404
    assert r.json() == {"erro": f"Transação {t['id']} não encontrada"}
    assert client.get("/transacoes").json() == []


@pytest.mark.parametrize(
    "metodo,corpo", [("get", None), ("put", VALIDA), ("delete", None)], ids=["get", "put", "delete"]
)
def test_id_inexistente_retorna_404(client, metodo, corpo):
    kwargs = {"json": corpo} if corpo else {}
    r = getattr(client, metodo)("/transacoes/999", **kwargs)
    assert r.status_code == 404
    assert r.json() == {"erro": "Transação 999 não encontrada"}


@pytest.mark.parametrize("metodo", ["get", "put", "delete"])
@pytest.mark.parametrize("id_", ["99999999999999999999", "-99999999999999999999"])
def test_id_fora_do_int64_retorna_404(client, metodo, id_):
    kwargs = {"json": VALIDA} if metodo == "put" else {}
    r = getattr(client, metodo)(f"/transacoes/{id_}", **kwargs)
    assert r.status_code == 404
    assert r.json() == {"erro": f"Transação {id_} não encontrada"}


def test_id_nao_inteiro_retorna_422(client):
    r = client.get("/transacoes/abc")
    assert r.status_code == 422
    assert r.json() == {"erro": "id: deve ser um número inteiro"}


INVALIDOS = [
    ({"valor": 0}, "valor: deve ser maior que 0"),
    ({"valor": -10}, "valor: deve ser maior que 0"),
    ({"valor": "abc"}, "valor: deve ser um número"),
    ({"valor": "50"}, "valor: deve ser um número"),
    ({"valor": True}, "valor: deve ser um número"),
    ({"valor": 0.001}, "valor: deve ser no mínimo 0.01"),  # arredondaria para 0 centavos
    ({"valor": 0.004}, "valor: deve ser no mínimo 0.01"),
    ({"valor": 1_000_000_000.01}, "valor: deve ser no máximo 1000000000"),
    ({"valor": 1e17}, "valor: deve ser no máximo 1000000000"),  # estouraria o INTEGER do SQLite
    ({"tipo": "despesa"}, "tipo: deve ser 'entrada' ou 'saida'"),
    ({"data": "2026-13-01"}, "data: deve ser uma data válida no formato YYYY-MM-DD"),
    ({"data": "2026-02-30"}, "data: deve ser uma data válida no formato YYYY-MM-DD"),
    ({"data": "01/10/2026"}, "data: deve ser uma data válida no formato YYYY-MM-DD"),
    ({"descricao": ""}, "descricao: não pode ser vazia"),
    ({"descricao": "   "}, "descricao: não pode ser vazia"),
]


@pytest.mark.parametrize("invalido,mensagem", INVALIDOS)
def test_post_invalido_retorna_422(client, invalido, mensagem):
    r = client.post("/transacoes", json={**VALIDA, **invalido})
    assert r.status_code == 422
    assert r.json() == {"erro": mensagem}
    assert client.get("/transacoes").json() == []


@pytest.mark.parametrize("invalido,mensagem", INVALIDOS)
def test_put_invalido_retorna_422_e_nao_altera(client, criar_transacao, invalido, mensagem):
    t = criar_transacao()
    r = client.put(f"/transacoes/{t['id']}", json={**VALIDA, **invalido})
    assert r.status_code == 422
    assert r.json() == {"erro": mensagem}
    assert client.get(f"/transacoes/{t['id']}").json() == t


def test_campo_ausente(client):
    r = client.post("/transacoes", json={"data": "2026-08-10"})
    assert r.status_code == 422
    assert r.json() == {"erro": "descricao: campo obrigatório"}


def test_json_invalido(client):
    r = client.post("/transacoes", content="{x", headers={"content-type": "application/json"})
    assert r.status_code == 422
    assert r.json() == {"erro": "corpo da requisição não é um JSON válido"}


def test_put_invalido_em_id_inexistente_retorna_422(client):
    """Decisão registrada: validação do corpo vem antes da checagem de existência."""
    r = client.put("/transacoes/999", json={**VALIDA, "valor": 0})
    assert r.status_code == 422
