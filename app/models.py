"""Schemas Pydantic de entrada e saída da API."""

from datetime import date
from typing import Literal

from pydantic import BaseModel


class TransacaoCreate(BaseModel):
    data: date
    descricao: str
    valor: float
    tipo: Literal["entrada", "saida"]


class Transacao(TransacaoCreate):
    id: int
