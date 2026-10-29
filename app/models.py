"""Schemas Pydantic de entrada e saída da API."""

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MSG_DATA_INVALIDA = "deve ser uma data válida no formato YYYY-MM-DD"


class TransacaoCreate(BaseModel):
    data: date
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    valor: float = Field(gt=0, allow_inf_nan=False, strict=True)
    tipo: Literal["entrada", "saida"]

    @field_validator("data", mode="before")
    @classmethod
    def validar_data_iso(cls, v):
        """Aceita só strings YYYY-MM-DD que formem uma data real."""
        if not isinstance(v, str) or not _DATA_ISO.match(v):
            raise ValueError(MSG_DATA_INVALIDA)
        try:
            return date.fromisoformat(v)
        except ValueError:
            raise ValueError(MSG_DATA_INVALIDA) from None


class Transacao(TransacaoCreate):
    id: int
