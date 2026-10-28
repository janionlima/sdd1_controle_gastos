"""Ponto de entrada da API: uvicorn app.main:app"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routes import transacoes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Controle de Gastos Pessoais", lifespan=lifespan)
app.include_router(transacoes.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Converte erros de validação para o formato do projeto: 422 {"erro": "..."}."""
    erro = exc.errors()[0]
    campo = ".".join(str(p) for p in erro["loc"] if p != "body")
    mensagem = f"{campo}: {erro['msg']}" if campo else erro["msg"]
    return JSONResponse(status_code=422, content={"erro": mensagem})
