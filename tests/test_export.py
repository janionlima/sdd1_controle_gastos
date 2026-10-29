"""Aula 6: GET /export.csv."""

import csv
import io

import pytest

COLUNAS = ["id", "data", "descricao", "valor", "tipo", "categoria_id", "categoria"]


def ler_csv(resposta) -> list[dict]:
    texto = resposta.content.decode("utf-8")
    assert texto.startswith("﻿"), "CSV deve começar com BOM UTF-8"
    leitor = csv.DictReader(io.StringIO(texto[1:]))
    assert leitor.fieldnames == COLUNAS
    return list(leitor)


@pytest.fixture
def massa(criar_categoria, criar_transacao):
    ali = criar_categoria("alimentação")
    tra = criar_categoria("transporte")
    return {
        "mercado": criar_transacao(data="2026-08-01", descricao="Mercado", valor=80, categoria_id=ali["id"]),
        "uber": criar_transacao(data="2026-08-10", descricao="Uber, ida", valor=12.5, categoria_id=tra["id"]),
        "salario": criar_transacao(data="2026-07-31", descricao="Salário", valor=3000, tipo="entrada"),
        "_ali": ali,
        "_tra": tra,
    }


def test_cabecalhos_http(client):
    r = client.get("/export.csv")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"] == 'attachment; filename="extrato.csv"'


def test_sem_transacoes_so_cabecalho(client):
    r = client.get("/export.csv")
    assert ler_csv(r) == []
    assert r.content.decode("utf-8") == "﻿" + ",".join(COLUNAS) + "\r\n"


def test_conteudo_e_ordem_da_api(client, massa):
    linhas = ler_csv(client.get("/export.csv"))
    assert [int(x["id"]) for x in linhas] == [t["id"] for t in client.get("/transacoes").json()]
    uber = next(x for x in linhas if x["id"] == str(massa["uber"]["id"]))
    assert uber == {
        "id": str(massa["uber"]["id"]),
        "data": "2026-08-10",
        "descricao": "Uber, ida",  # vírgula na descrição: o csv cuida das aspas
        "valor": "12.50",          # sempre 2 casas
        "tipo": "saida",
        "categoria_id": str(massa["_tra"]["id"]),
        "categoria": "transporte",
    }


def test_acentos_e_sem_categoria(client, massa):
    linhas = {x["descricao"]: x for x in ler_csv(client.get("/export.csv"))}
    assert linhas["Mercado"]["categoria"] == "alimentação"
    assert linhas["Salário"]["categoria_id"] == ""
    assert linhas["Salário"]["categoria"] == ""
    assert linhas["Salário"]["valor"] == "3000.00"


@pytest.mark.parametrize(
    "params,descricoes",
    [
        ({"categoria": "transporte"}, ["Uber, ida"]),
        ({"data_inicio": "2026-08-01", "data_fim": "2026-08-31"}, ["Uber, ida", "Mercado"]),
        ({"valor_min": 50}, ["Mercado", "Salário"]),
        ({"categoria": "alimentação", "data_inicio": "2026-08-01", "valor_max": 100}, ["Mercado"]),
        ({"categoria": "lazer"}, []),
    ],
    ids=["categoria", "periodo", "valor", "combinado", "categoria-inexistente"],
)
def test_filtros_afetam_o_conteudo(client, massa, params, descricoes):
    r = client.get("/export.csv", params=params)
    assert r.status_code == 200
    assert [x["descricao"] for x in ler_csv(r)] == descricoes
    # Mesmo conjunto que a API JSON devolve com os mesmos filtros.
    assert [x["descricao"] for x in client.get("/transacoes", params=params).json()] == descricoes


@pytest.mark.parametrize(
    "params,mensagem",
    [
        ({"data_inicio": "2026-09-01", "data_fim": "2026-08-01"}, "data_inicio: não pode ser posterior a data_fim"),
        ({"valor_min": "abc"}, "valor_min: deve ser um número"),
        ({"data_inicial": "2026-08-01"}, "data_inicial: parâmetro desconhecido"),
    ],
)
def test_filtro_invalido_retorna_422_json(client, params, mensagem):
    r = client.get("/export.csv", params=params)
    assert r.status_code == 422
    assert r.headers["content-type"] == "application/json"
    assert r.json() == {"erro": mensagem}


@pytest.mark.parametrize("perigoso", ["=HYPERLINK(\"http://x\")", "+1+1", "-2", "@SUM(A1)"])
def test_texto_que_vira_formula_e_neutralizado(client, criar_transacao, criar_categoria, perigoso):
    cat = criar_categoria(perigoso)
    criar_transacao(descricao=perigoso, categoria_id=cat["id"])
    [linha] = ler_csv(client.get("/export.csv"))
    assert linha["descricao"] == "'" + perigoso
    assert linha["categoria"] == "'" + perigoso
    # A API JSON continua devolvendo o texto original.
    assert client.get("/transacoes").json()[0]["descricao"] == perigoso
