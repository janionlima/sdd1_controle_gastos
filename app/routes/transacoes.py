"""Rotas de transações."""

from fastapi import APIRouter

from app.database import criar_transacao, listar_transacoes
from app.models import Transacao, TransacaoCreate

router = APIRouter(prefix="/transacoes", tags=["transacoes"])


@router.post("", status_code=201, response_model=Transacao)
def criar(payload: TransacaoCreate):
    return criar_transacao(payload.data.isoformat(), payload.descricao, payload.valor, payload.tipo)


@router.get("", response_model=list[Transacao])
def listar():
    return listar_transacoes()
