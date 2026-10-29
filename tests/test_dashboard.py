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


def test_dashboard_nao_usa_innerhtml_com_dados_da_api(client):
    assert "innerHTML" not in client.get("/").text


def test_dashboard_fora_da_documentacao(client):
    assert "/" not in client.get("/openapi.json").json()["paths"]
