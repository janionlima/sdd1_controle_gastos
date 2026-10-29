"""Rotas de transações."""

from fastapi import APIRouter, HTTPException, Response

from app.database import (
    atualizar_transacao,
    buscar_transacao,
    criar_transacao,
    excluir_transacao,
    listar_transacoes,
)
from app.models import Transacao, TransacaoCreate

router = APIRouter(prefix="/transacoes", tags=["transacoes"])


def _nao_encontrada(id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Transação {id} não encontrada")


@router.post("", status_code=201, response_model=Transacao)
def criar(payload: TransacaoCreate):
    return criar_transacao(payload.data.isoformat(), payload.descricao, payload.valor, payload.tipo)


@router.get("", response_model=list[Transacao])
def listar():
    return listar_transacoes()


@router.get("/{id}", response_model=Transacao)
def buscar(id: int):
    transacao = buscar_transacao(id)
    if transacao is None:
        raise _nao_encontrada(id)
    return transacao


@router.put("/{id}", response_model=Transacao)
def atualizar(id: int, payload: TransacaoCreate):
    transacao = atualizar_transacao(
        id, payload.data.isoformat(), payload.descricao, payload.valor, payload.tipo
    )
    if transacao is None:
        raise _nao_encontrada(id)
    return transacao


@router.delete("/{id}", status_code=204)
def excluir(id: int):
    if not excluir_transacao(id):
        raise _nao_encontrada(id)
    return Response(status_code=204)
