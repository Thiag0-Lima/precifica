from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Configuracao

router = APIRouter(prefix="/config", tags=["Configurações"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def config_page(request: Request, db: Session = Depends(get_db)):
    config = db.query(Configuracao).first()
    if not config:
        config = Configuracao()
        db.add(config)
        db.commit()
        db.refresh(config)
    return templates.TemplateResponse("config.html", {
        "request": request,
        "config": config,
        "active": "config"
    })


@router.post("")
def salvar_config(
    custos_invisiveis_pct: float = Form(...),
    taxa_horaria: float = Form(...),
    margem_minima_alerta: float = Form(...),
    embalagem_padrao: float = Form(...),
    taxa_cartao_pct: float = Form(...),
    db: Session = Depends(get_db)
):
    config = db.query(Configuracao).first()
    if not config:
        config = Configuracao()
        db.add(config)

    config.custos_invisiveis_pct = custos_invisiveis_pct
    config.taxa_horaria = taxa_horaria
    config.margem_minima_alerta = margem_minima_alerta
    config.embalagem_padrao = embalagem_padrao
    config.taxa_cartao_pct = taxa_cartao_pct
    db.commit()
    return RedirectResponse(url="/config", status_code=303)
