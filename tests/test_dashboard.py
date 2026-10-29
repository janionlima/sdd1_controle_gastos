"""Aula 6: GET / serve o dashboard HTML."""


def test_dashboard_e_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")


def test_dashboard_tem_grafico_e_consome_endpoints(client):
    html = client.get("/").text
    assert "<canvas" in html
    assert "chart.js@4.4.1" in html and 'integrity="sha384-' in html  # versão fixa + SRI
    assert 'fetch(url)' in html
    assert '"/saldo"' in html  # saldo atual
    assert "/resumo?mes=" in html  # gastos por categoria
    assert "/export.csv" in html


def test_dashboard_tem_formulario_de_nova_transacao(client):
    html = client.get("/").text
    assert 'id="form-transacao"' in html
    for campo in ('name="data"', 'name="descricao"', 'name="valor"', 'name="tipo"', 'name="categoria_id"'):
        assert campo in html
    assert 'fetch("/transacoes"' in html and 'method: "POST"' in html
    assert 'buscar("/categorias")' in html  # opções de categoria vêm da API


def test_dashboard_permite_criar_categoria(client):
    html = client.get("/").text
    assert "+ Nova categoria…" in html
    assert 'id="f-nova-categoria"' in html
    assert 'fetch("/categorias"' in html  # POST da categoria nova antes da transação


def test_dashboard_nao_usa_innerhtml_com_dados_da_api(client):
    assert "innerHTML" not in client.get("/").text


def test_dashboard_fora_da_documentacao(client):
    assert "/" not in client.get("/openapi.json").json()["paths"]
