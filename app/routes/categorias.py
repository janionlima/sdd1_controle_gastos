"""Rotas de categorias."""

from fastapi import APIRouter, HTTPException

from app.database import criar_categoria, listar_categorias
from app.models import Categoria, CategoriaCreate

router = APIRouter(prefix="/categorias", tags=["categorias"])


@router.post("", status_code=201, response_model=Categoria)
def criar(payload: CategoriaCreate):
    categoria = criar_categoria(payload.nome)
    if categoria is None:
        raise HTTPException(status_code=422, detail=f"nome: categoria '{payload.nome}' já existe")
    return categoria


@router.get("", response_model=list[Categoria])
def listar():
    return listar_categorias()
