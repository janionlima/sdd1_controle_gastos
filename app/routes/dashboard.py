"""Mini-dashboard: página HTML estática que consome /saldo e /resumo."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

_DASHBOARD = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"


@router.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(_DASHBOARD, media_type="text/html")
