from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Receita, Configuracao

router = APIRouter(prefix="/calculadora", tags=["Calculadora"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def calculadora_page(request: Request, db: Session = Depends(get_db)):
    receitas = db.query(Receita).order_by(Receita.nome).all()
    config = db.query(Configuracao).first()
    return templates.TemplateResponse("calculadora.html", {
        "request": request,
        "receitas": receitas,
        "config": config,
        "resultado": None,
        "active": "calculadora"
    })


@router.post("")
def calcular(
    request: Request,
    receita_id: int = Form(...),
    rendimento_desejado: float = Form(...),
    margem_desejada: Optional[str] = Form(None),
    preco_alvo: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Converte strings vazias para None e depois para float
    def to_float(value):
        if value is None or str(value).strip() == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    margem = to_float(margem_desejada)
    preco = to_float(preco_alvo)

    receita = db.query(Receita).filter(Receita.id == receita_id).first()
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    config = db.query(Configuracao).first()
    if not config:
        config = Configuracao()

    # Fator de escala
    fator = rendimento_desejado / receita.rendimento_qtd

    # Itens escalados
    itens = []
    custo_insumos = 0.0
    for item in receita.itens:
        qtd_escalada = item.quantidade * fator
        custo = qtd_escalada * item.insumo.custo_unitario
        custo_insumos += custo

        # Mostra na unidade original do cadastro do item
        un_exibicao = item.unidade
        qtd_exibicao = qtd_escalada
        if item.unidade in ("kg", "L"):
            qtd_exibicao = qtd_escalada / 1000

        itens.append({
            "nome": item.insumo.nome,
            "quantidade": round(qtd_exibicao, 2),
            "unidade": un_exibicao,
            "custo": round(custo, 2)
        })

    # Custos adicionais
    custo_invisiveis = custo_insumos * (config.custos_invisiveis_pct / 100)
    horas = (receita.tempo_preparo_min / 60) * fator
    custo_mao_obra = horas * config.taxa_horaria
    custo_embalagem = config.embalagem_padrao * rendimento_desejado

    custo_total = custo_insumos + custo_invisiveis + custo_mao_obra + custo_embalagem
    custo_unitario = custo_total / rendimento_desejado if rendimento_desejado else 0

    # Simulador
    preco_sugerido = None
    lucro = None
    margem_real = None

    if margem is not None and margem > 0:
        # Preço = custo / (1 - margem/100)
        preco_sugerido = custo_unitario / (1 - (margem / 100))
        lucro = preco_sugerido - custo_unitario
        margem_real = margem

    if preco is not None and preco > 0:
        lucro = preco - custo_unitario
        margem_real = (lucro / preco) * 100 if preco else 0
        preco_sugerido = preco

    resultado = {
        "receita_nome": receita.nome,
        "rendimento_desejado": rendimento_desejado,
        "rendimento_unidade": receita.rendimento_unidade,
        "fator": round(fator, 3),
        "itens": itens,
        "custo_insumos": round(custo_insumos, 2),
        "custo_invisiveis": round(custo_invisiveis, 2),
        "custo_mao_obra": round(custo_mao_obra, 2),
        "custo_embalagem": round(custo_embalagem, 2),
        "custo_total": round(custo_total, 2),
        "custo_unitario": round(custo_unitario, 2),
        "preco_sugerido": round(preco_sugerido, 2) if preco_sugerido else None,
        "lucro": round(lucro, 2) if lucro is not None else None,
        "margem_real": round(margem_real, 1) if margem_real is not None else None,
        "margem_minima": config.margem_minima_alerta
    }

    receitas = db.query(Receita).order_by(Receita.nome).all()
    return templates.TemplateResponse("calculadora.html", {
        "request": request,
        "receitas": receitas,
        "config": config,
        "resultado": resultado,
        "receita_selecionada": receita_id,
        "rendimento_desejado": rendimento_desejado,
        "margem_desejada": margem,
        "preco_alvo": preco,
        "active": "calculadora"
    })
