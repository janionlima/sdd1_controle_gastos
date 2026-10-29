"""Schemas Pydantic de entrada e saída da API."""

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

_DATA_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
MSG_DATA_INVALIDA = "deve ser uma data válida no formato YYYY-MM-DD"
_MES = re.compile(r"\d{4}-(0[1-9]|1[0-2])")

TextoNaoVazio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _validar_data_iso(v):
    """Aceita só strings YYYY-MM-DD que formem uma data real."""
    if not isinstance(v, str) or not _DATA_ISO.fullmatch(v):
        raise ValueError(MSG_DATA_INVALIDA)
    try:
        return date.fromisoformat(v)
    except ValueError:
        raise ValueError(MSG_DATA_INVALIDA) from None


DataISO = Annotated[date, BeforeValidator(_validar_data_iso)]


def _validar_mes(v: str) -> str:
    if not _MES.fullmatch(v):
        raise ValueError("deve ser um mês válido no formato YYYY-MM")
    return v


Mes = Annotated[str, AfterValidator(_validar_mes)]


class CategoriaCreate(BaseModel):
    nome: TextoNaoVazio

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        """Nome só com dígitos seria confundido com id no filtro `?categoria=`."""
        if v.isdigit():
            raise ValueError("não pode conter apenas dígitos")
        return v


class Categoria(CategoriaCreate):
    id: int


class TransacaoCreate(BaseModel):
    data: DataISO
    descricao: TextoNaoVazio
    valor: float = Field(gt=0, allow_inf_nan=False, strict=True)
    tipo: Literal["entrada", "saida"]
    categoria_id: int | None = Field(default=None, strict=True)


class Transacao(TransacaoCreate):
    id: int


class FiltrosTransacao(BaseModel):
    """Query params de `GET /transacoes`: todos opcionais, combinados por E; limites inclusivos."""

    categoria: str | None = Field(default=None, min_length=1, description="Nome ou id da categoria")
    data_inicio: DataISO | None = None
    data_fim: DataISO | None = None
    valor_min: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    valor_max: float | None = Field(default=None, gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validar_faixas(self):
        if self.data_inicio and self.data_fim and self.data_inicio > self.data_fim:
            raise ValueError("data_inicio: não pode ser posterior a data_fim")
        if self.valor_min and self.valor_max and self.valor_min > self.valor_max:
            raise ValueError("valor_min: não pode ser maior que valor_max")
        return self


class Saldo(BaseModel):
    entradas: float
    saidas: float
    saldo: float


class TotalCategoria(BaseModel):
    categoria: str | None  # None = saídas sem categoria
    total: float


class Resumo(BaseModel):
    # Campos na ordem do contrato da spec: { mes, entradas, saidas, saldo, por_categoria }.
    mes: str
    entradas: float
    saidas: float
    saldo: float
    por_categoria: list[TotalCategoria]
