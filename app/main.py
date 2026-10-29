"""Ponto de entrada da API: uvicorn app.main:app"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routes import categorias, dashboard, export, resumo, transacoes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Controle de Gastos Pessoais", lifespan=lifespan)
app.include_router(transacoes.router)
app.include_router(categorias.router)
app.include_router(resumo.router)
app.include_router(export.router)
app.include_router(dashboard.router)

# Tradução dos tipos de erro do Pydantic para mensagens do projeto.
_MENSAGENS = {
    "greater_than": "deve ser maior que 0",
    "float_parsing": "deve ser um número",
    "float_type": "deve ser um número",
    "finite_number": "deve ser um número",
    "literal_error": "deve ser 'entrada' ou 'saida'",
    "string_too_short": "não pode ser vazia",
    "int_parsing": "deve ser um número inteiro",
    "int_type": "deve ser um número inteiro",
    "missing": "campo obrigatório",
    "less_than_equal": "deve ser no máximo {le}",
    "extra_forbidden": "parâmetro desconhecido",
}


def _mensagem_validacao(erro: dict) -> str:
    if erro["type"] == "json_invalid":
        return "corpo da requisição não é um JSON válido"
    campo = ".".join(str(p) for p in erro["loc"] if p not in ("body", "path", "query"))
    if not campo and erro["type"] == "missing":
        return "corpo da requisição é obrigatório"
    if erro["type"] == "value_error":
        msg = str(erro["ctx"]["error"])
    elif erro["type"] in _MENSAGENS:
        # Mensagens do projeto podem usar o contexto do erro (ex.: {le} = limite máximo).
        ctx = {k: int(v) if isinstance(v, float) and v.is_integer() else v for k, v in erro.get("ctx", {}).items()}
        msg = _MENSAGENS[erro["type"]].format(**ctx)
    else:
        msg = erro["msg"]
    return f"{campo}: {msg}" if campo else msg


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Converte erros de validação para o formato do projeto: 422 {"erro": "..."}."""
    return JSONResponse(status_code=422, content={"erro": _mensagem_validacao(exc.errors()[0])})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    """Mantém o status (404, 400...) mas usa o corpo {"erro": "..."}."""
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail}, headers=exc.headers)
