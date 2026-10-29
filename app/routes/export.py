"""Exportação do extrato em CSV (mesmos filtros de GET /transacoes)."""

import csv
import io
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.database import listar_categorias, listar_transacoes
from app.models import FiltrosTransacao

router = APIRouter(tags=["export"])

COLUNAS = ["id", "data", "descricao", "valor", "tipo", "categoria_id", "categoria"]

# Texto que começa com estes caracteres vira fórmula no Excel/Sheets (CSV injection).
_INICIO_DE_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def _texto_seguro(texto: str) -> str:
    return "'" + texto if texto.startswith(_INICIO_DE_FORMULA) else texto


@router.get("/export.csv", response_class=Response)
def exportar_csv(filtros: Annotated[FiltrosTransacao, Query()]):
    """Extrato em CSV (RFC 4180, UTF-8 com BOM), na mesma ordem e com os mesmos filtros da API."""
    nomes = {c["id"]: c["nome"] for c in listar_categorias()}
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(COLUNAS)
    for t in listar_transacoes(filtros):
        categoria = nomes.get(t["categoria_id"], "")
        writer.writerow([
            t["id"],
            t["data"],
            _texto_seguro(t["descricao"]),
            f"{t['valor']:.2f}",
            t["tipo"],
            "" if t["categoria_id"] is None else t["categoria_id"],
            _texto_seguro(categoria),
        ])
    return Response(
        content="﻿" + buffer.getvalue(),  # BOM: o Excel reconhece UTF-8 e mostra os acentos
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="extrato.csv"'},
    )
