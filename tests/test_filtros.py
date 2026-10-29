"""Aulas 3 e 5: filtros de GET /transacoes (categoria, período, faixa de valor)."""

import pytest

from tests.conftest import ids


@pytest.fixture
def massa(criar_categoria, criar_transacao):
    """Transações espalhadas por categoria, data e valor; retorna {apelido: transação}."""
    ali = criar_categoria("alimentacao")
    tra = criar_categoria("transporte")
    t = {
        "mercado_jul": criar_transacao(data="2026-07-31", valor=80, categoria_id=ali["id"]),
        "mercado_ago": criar_transacao(data="2026-08-01", valor=80, categoria_id=ali["id"]),
        "padaria_ago": criar_transacao(data="2026-08-15", valor=12.5, categoria_id=ali["id"]),
        "jantar_ago": criar_transacao(data="2026-08-31", valor=200, categoria_id=ali["id"]),
        "uber_ago": criar_transacao(data="2026-08-10", valor=80, categoria_id=tra["id"]),
        "sem_cat_ago": criar_transacao(data="2026-08-20", valor=80),
        "mercado_set": criar_transacao(data="2026-09-01", valor=80, categoria_id=ali["id"]),
    }
    t["_ali"], t["_tra"] = ali, tra
    return t


def esperados(massa, *apelidos):
    """Ids na ordem da API: data DESC, id DESC."""
    ts = sorted((massa[a] for a in apelidos), key=lambda x: (x["data"], x["id"]), reverse=True)
    return [x["id"] for x in ts]


def test_todos_os_filtros_combinados(client, massa):
    r = client.get(
        "/transacoes",
        params={"categoria": "alimentacao", "data_inicio": "2026-08-01", "data_fim": "2026-08-31",
                "valor_min": 50, "valor_max": 100},
    )
    assert r.status_code == 200
    # Fora: mercado_jul/mercado_set (período), padaria/jantar (valor), uber/sem_cat (categoria).
    assert ids(r) == esperados(massa, "mercado_ago")


def test_todos_os_filtros_combinados_com_categoria_por_id(client, massa):
    r = client.get(
        "/transacoes",
        params={"categoria": massa["_ali"]["id"], "data_inicio": "2026-08-01", "data_fim": "2026-08-31",
                "valor_min": 50, "valor_max": 100},
    )
    assert ids(r) == esperados(massa, "mercado_ago")


def test_combinacao_parcial(client, massa):
    r = client.get("/transacoes", params={"data_inicio": "2026-08-01", "data_fim": "2026-08-31", "valor_min": 80})
    assert ids(r) == esperados(massa, "mercado_ago", "jantar_ago", "uber_ago", "sem_cat_ago")


def test_sem_filtros_lista_tudo(client, massa):
    assert len(client.get("/transacoes").json()) == 7


@pytest.mark.parametrize(
    "params,apelidos",
    [
        ({"categoria": "transporte"}, ["uber_ago"]),
        ({"categoria": "ALIMENTACAO"}, ["mercado_jul", "mercado_ago", "padaria_ago", "jantar_ago", "mercado_set"]),
        ({"data_inicio": "2026-08-31"}, ["jantar_ago", "mercado_set"]),
        ({"data_fim": "2026-08-01"}, ["mercado_jul", "mercado_ago"]),
        ({"valor_min": 200}, ["jantar_ago"]),
        ({"valor_max": 12.5}, ["padaria_ago"]),
        ({"data_inicio": "2026-08-15", "data_fim": "2026-08-15"}, ["padaria_ago"]),
        ({"valor_min": "80", "valor_max": "80"},
         ["mercado_jul", "mercado_ago", "uber_ago", "sem_cat_ago", "mercado_set"]),
    ],
    ids=["categoria", "categoria-maiusculas", "data_inicio-inclusivo", "data_fim-inclusivo",
         "valor_min-inclusivo", "valor_max-inclusivo", "periodo-de-um-dia", "faixa-de-um-valor"],
)
def test_filtro_isolado(client, massa, params, apelidos):
    r = client.get("/transacoes", params=params)
    assert r.status_code == 200
    assert ids(r) == esperados(massa, *apelidos)


def test_categoria_por_id(client, massa):
    r = client.get("/transacoes", params={"categoria": massa["_tra"]["id"]})
    assert ids(r) == esperados(massa, "uber_ago")


def test_categoria_ignora_espacos_nas_pontas(client, massa):
    r = client.get("/transacoes", params={"categoria": "  transporte  "})
    assert ids(r) == esperados(massa, "uber_ago")


@pytest.mark.parametrize(
    "params,apelidos",
    [
        # Limites fora do centavo arredondam para DENTRO da faixa (inclusiva).
        ({"valor_max": 12.499}, []),                 # 12.50 > 12.499
        ({"valor_min": 12.501, "valor_max": 79.999}, []),
        ({"valor_min": 12.491, "valor_max": 12.509}, ["padaria_ago"]),
        ({"valor_min": 199.999}, ["jantar_ago"]),
        ({"valor_min": 0.1 + 0.2, "valor_max": 12.5}, ["padaria_ago"]),  # 0.30000000000000004
    ],
    ids=["max-abaixo", "faixa-sem-centavo", "faixa-em-volta", "min-quase", "ruido-float"],
)
def test_limites_de_valor_fora_do_centavo(client, massa, params, apelidos):
    r = client.get("/transacoes", params=params)
    assert r.status_code == 200
    assert ids(r) == esperados(massa, *apelidos)


@pytest.mark.parametrize("categoria", ["lazer", "999", "alimentação", "99999999999999999999", "²", "١"])
def test_categoria_inexistente_retorna_lista_vazia(client, massa, categoria):
    r = client.get("/transacoes", params={"categoria": categoria})
    assert r.status_code == 200
    assert r.json() == []


def test_filtros_sem_resultado_retornam_lista_vazia(client, massa):
    r = client.get("/transacoes", params={"categoria": "transporte", "valor_min": 1000})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.parametrize(
    "params,mensagem",
    [
        ({"data_inicio": "2026-09-01", "data_fim": "2026-08-01"}, "data_inicio: não pode ser posterior a data_fim"),
        ({"valor_min": 100, "valor_max": 50}, "valor_min: não pode ser maior que valor_max"),
        ({"data_inicio": "2026-02-30"}, "data_inicio: deve ser uma data válida no formato YYYY-MM-DD"),
        ({"data_fim": "01/08/2026"}, "data_fim: deve ser uma data válida no formato YYYY-MM-DD"),
        ({"valor_min": "abc"}, "valor_min: deve ser um número"),
        ({"valor_max": "nan"}, "valor_max: deve ser um número"),
        ({"valor_min": 0}, "valor_min: deve ser maior que 0"),
        ({"valor_max": -5}, "valor_max: deve ser maior que 0"),
        ({"categoria": ""}, "categoria: não pode ser vazia"),
        ({"categoria": "   "}, "categoria: não pode ser vazia"),
        ({"valor_min": 1e300}, "valor_min: deve ser no máximo 1000000000"),
        ({"valor_max": 1e17}, "valor_max: deve ser no máximo 1000000000"),
        ({"data_inicial": "2026-08-01"}, "data_inicial: parâmetro desconhecido"),
    ],
    ids=["periodo-invertido", "faixa-invertida", "data_inicio-inexistente", "data_fim-malformada",
         "valor_min-texto", "valor_max-nan", "valor_min-zero", "valor_max-negativo", "categoria-vazia",
         "categoria-so-espacos", "valor_min-enorme", "valor_max-enorme", "parametro-desconhecido"],
)
def test_filtro_invalido_retorna_422(client, params, mensagem):
    r = client.get("/transacoes", params=params)
    assert r.status_code == 422
    assert r.json() == {"erro": mensagem}


def test_filtro_nao_executa_sql_injetado(client, massa):
    r = client.get("/transacoes", params={"categoria": "x' OR '1'='1"})
    assert r.status_code == 200
    assert r.json() == []
    assert len(client.get("/transacoes").json()) == 7
