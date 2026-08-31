from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Insumo
from ..schemas import InsumoCreate, InsumoUpdate

router = APIRouter(prefix="/insumos", tags=["Insumos"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def listar_insumos(request: Request, db: Session = Depends(get_db)):
    insumos = db.query(Insumo).order_by(Insumo.nome).all()
    return templates.TemplateResponse("insumos.html", {
        "request": request,
        "insumos": insumos,
        "active": "insumos"
    })


@router.post("")
def criar_insumo(
    nome: str = Form(...),
    quantidade_embalagem: float = Form(...),
    unidade: str = Form(...),
    preco: float = Form(...),
    fornecedor: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    insumo = Insumo(
        nome=nome.strip(),
        quantidade_embalagem=quantidade_embalagem,
        unidade=unidade,
        preco=preco,
        fornecedor=fornecedor.strip() if fornecedor else None
    )
    db.add(insumo)
    db.commit()
    return RedirectResponse(url="/insumos", status_code=303)


@router.post("/{insumo_id}/editar")
def editar_insumo(
    insumo_id: int,
    nome: str = Form(...),
    quantidade_embalagem: float = Form(...),
    unidade: str = Form(...),
    preco: float = Form(...),
    fornecedor: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")

    insumo.nome = nome.strip()
    insumo.quantidade_embalagem = quantidade_embalagem
    insumo.unidade = unidade
    insumo.preco = preco
    insumo.fornecedor = fornecedor.strip() if fornecedor else None
    db.commit()
    return RedirectResponse(url="/insumos", status_code=303)


@router.post("/{insumo_id}/excluir")
def excluir_insumo(insumo_id: int, db: Session = Depends(get_db)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    db.delete(insumo)
    db.commit()
    return RedirectResponse(url="/insumos", status_code=303)
