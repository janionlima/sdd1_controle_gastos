"""Rotas de cálculos agregados: saldo total e resumo mensal."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.database import calcular_resumo, calcular_saldo
from app.models import Mes, Resumo, Saldo

router = APIRouter(tags=["resumo"])


@router.get("/saldo", response_model=Saldo)
def saldo():
    return calcular_saldo()


@router.get("/resumo", response_model=Resumo)
def resumo(mes: Annotated[Mes, Query(description="Mês no formato YYYY-MM")]):
    # Annotated[...] é necessário: com `mes: Mes = Query(...)` o FastAPI descarta o AfterValidator de `Mes`.
    return calcular_resumo(mes)
