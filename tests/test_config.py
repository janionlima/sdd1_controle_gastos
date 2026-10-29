"""Aula 6: `python -m app` lê host e porta do ambiente."""

import app.__main__ as entrada


def chamadas_de_uvicorn(monkeypatch) -> list[dict]:
    chamadas = []
    monkeypatch.setattr(entrada.uvicorn, "run", lambda alvo, **kw: chamadas.append({"alvo": alvo, **kw}))
    return chamadas


def test_usa_host_e_porta_do_ambiente(monkeypatch):
    chamadas = chamadas_de_uvicorn(monkeypatch)
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9123")
    entrada.main()
    assert chamadas == [{"alvo": "app.main:app", "host": "0.0.0.0", "port": 9123}]


def test_padroes_sem_ambiente(monkeypatch):
    chamadas = chamadas_de_uvicorn(monkeypatch)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    entrada.main()
    assert chamadas == [{"alvo": "app.main:app", "host": "127.0.0.1", "port": 8000}]
