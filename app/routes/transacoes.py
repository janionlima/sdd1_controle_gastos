"""Rotas de transações."""

from fastapi import APIRouter, HTTPException, Query, Response

from app.database import (
    atualizar_transacao,
    buscar_categoria,
    buscar_transacao,
    criar_transacao,
    excluir_transacao,
    listar_transacoes,
)
from app.models import Transacao, TransacaoCreate

router = APIRouter(prefix="/transacoes", tags=["transacoes"])


def _nao_encontrada(id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Transação {id} não encontrada")


def _validar_categoria(categoria_id: int | None) -> None:
    """Regra de negócio: categoria_id informado precisa existir (422)."""
    if categoria_id is not None and buscar_categoria(categoria_id) is None:
        raise HTTPException(status_code=422, detail=f"categoria_id: categoria {categoria_id} não existe")


@router.post("", status_code=201, response_model=Transacao)
def criar(payload: TransacaoCreate):
    _validar_categoria(payload.categoria_id)
    return criar_transacao(
        payload.data.isoformat(), payload.descricao, payload.valor, payload.tipo, payload.categoria_id
    )


@router.get("", response_model=list[Transacao])
def listar(categoria: str | None = Query(None, min_length=1, description="Nome ou id da categoria")):
    return listar_transacoes(categoria)


@router.get("/{id}", response_model=Transacao)
def buscar(id: int):
    transacao = buscar_transacao(id)
    if transacao is None:
        raise _nao_encontrada(id)
    return transacao


@router.put("/{id}", response_model=Transacao)
def atualizar(id: int, payload: TransacaoCreate):
    _validar_categoria(payload.categoria_id)
    transacao = atualizar_transacao(
        id, payload.data.isoformat(), payload.descricao, payload.valor, payload.tipo, payload.categoria_id
    )
    if transacao is None:
        raise _nao_encontrada(id)
    return transacao


@router.delete("/{id}", status_code=204)
def excluir(id: int):
    if not excluir_transacao(id):
        raise _nao_encontrada(id)
    return Response(status_code=204)
