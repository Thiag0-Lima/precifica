from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from ..database import get_db
from ..models import Receita, ReceitaItem, Insumo

router = APIRouter(prefix="/receitas", tags=["Receitas"])
templates = Jinja2Templates(directory="app/templates")


def _calcular_custo_receita(receita: Receita) -> tuple[float, float]:
    """Retorna (custo_total, custo_unitario)"""
    total = 0.0
    for item in receita.itens:
        # quantidade já está na unidade base
        custo = item.quantidade * item.insumo.custo_unitario
        total += custo
    unitario = total / receita.rendimento_qtd if receita.rendimento_qtd else 0
    return round(total, 2), round(unitario, 2)


@router.get("")
def listar_receitas(request: Request, db: Session = Depends(get_db)):
    receitas = db.query(Receita).order_by(Receita.nome).all()
    # adiciona custo calculado
    for r in receitas:
        r.custo_total, r.custo_unitario = _calcular_custo_receita(r)
    return templates.TemplateResponse("receitas.html", {
        "request": request,
        "receitas": receitas,
        "active": "receitas"
    })


@router.get("/nova")
def form_nova_receita(request: Request, db: Session = Depends(get_db)):
    insumos = db.query(Insumo).order_by(Insumo.nome).all()
    return templates.TemplateResponse("receita_form.html", {
        "request": request,
        "receita": None,
        "insumos": insumos,
        "active": "receitas"
    })


@router.get("/{receita_id}/editar")
def form_editar_receita(receita_id: int, request: Request, db: Session = Depends(get_db)):
    receita = db.query(Receita).filter(Receita.id == receita_id).first()
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    insumos = db.query(Insumo).order_by(Insumo.nome).all()
    return templates.TemplateResponse("receita_form.html", {
        "request": request,
        "receita": receita,
        "insumos": insumos,
        "active": "receitas"
    })


@router.post("")
async def criar_receita(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    nome = form.get("nome", "").strip()
    categoria = form.get("categoria", "").strip() or None
    rendimento_qtd = float(form.get("rendimento_qtd", 1))
    rendimento_unidade = form.get("rendimento_unidade", "un")
    tempo_preparo_min = int(form.get("tempo_preparo_min") or 0)
    observacao = form.get("observacao", "").strip() or None

    receita = Receita(
        nome=nome,
        categoria=categoria,
        rendimento_qtd=rendimento_qtd,
        rendimento_unidade=rendimento_unidade,
        tempo_preparo_min=tempo_preparo_min,
        observacao=observacao
    )
    db.add(receita)
    db.flush()  # pega o id

    # Itens (vêm como arrays)
    insumo_ids = form.getlist("insumo_id")
    quantidades = form.getlist("quantidade")
    unidades = form.getlist("unidade")

    for i, insumo_id in enumerate(insumo_ids):
        if not insumo_id:
            continue
        qtd = float(quantidades[i])
        un = unidades[i]
        # Converte para unidade base
        qtd_base = qtd * 1000 if un in ("kg", "L") else qtd
        item = ReceitaItem(
            receita_id=receita.id,
            insumo_id=int(insumo_id),
            quantidade=qtd_base,
            unidade=un
        )
        db.add(item)

    db.commit()
    return RedirectResponse(url="/receitas", status_code=303)


@router.post("/{receita_id}/editar")
async def editar_receita(receita_id: int, request: Request, db: Session = Depends(get_db)):
    receita = db.query(Receita).filter(Receita.id == receita_id).first()
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    form = await request.form()
    receita.nome = form.get("nome", "").strip()
    receita.categoria = form.get("categoria", "").strip() or None
    receita.rendimento_qtd = float(form.get("rendimento_qtd", 1))
    receita.rendimento_unidade = form.get("rendimento_unidade", "un")
    receita.tempo_preparo_min = int(form.get("tempo_preparo_min") or 0)
    receita.observacao = form.get("observacao", "").strip() or None

    # Remove itens antigos
    for item in receita.itens:
        db.delete(item)
    db.flush()

    insumo_ids = form.getlist("insumo_id")
    quantidades = form.getlist("quantidade")
    unidades = form.getlist("unidade")

    for i, insumo_id in enumerate(insumo_ids):
        if not insumo_id:
            continue
        qtd = float(quantidades[i])
        un = unidades[i]
        qtd_base = qtd * 1000 if un in ("kg", "L") else qtd
        item = ReceitaItem(
            receita_id=receita.id,
            insumo_id=int(insumo_id),
            quantidade=qtd_base,
            unidade=un
        )
        db.add(item)

    db.commit()
    return RedirectResponse(url="/receitas", status_code=303)


@router.post("/{receita_id}/excluir")
def excluir_receita(receita_id: int, db: Session = Depends(get_db)):
    receita = db.query(Receita).filter(Receita.id == receita_id).first()
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    db.delete(receita)
    db.commit()
    return RedirectResponse(url="/receitas", status_code=303)


@router.post("/{receita_id}/duplicar")
def duplicar_receita(receita_id: int, db: Session = Depends(get_db)):
    original = db.query(Receita).filter(Receita.id == receita_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    nova = Receita(
        nome=f"{original.nome} (cópia)",
        categoria=original.categoria,
        rendimento_qtd=original.rendimento_qtd,
        rendimento_unidade=original.rendimento_unidade,
        tempo_preparo_min=original.tempo_preparo_min,
        observacao=original.observacao
    )
    db.add(nova)
    db.flush()

    for item in original.itens:
        novo_item = ReceitaItem(
            receita_id=nova.id,
            insumo_id=item.insumo_id,
            quantidade=item.quantidade,
            unidade=item.unidade
        )
        db.add(novo_item)

    db.commit()
    return RedirectResponse(url=f"/receitas/{nova.id}/editar", status_code=303)


@router.get("/{receita_id}/pdf")
def exportar_pdf(receita_id: int, db: Session = Depends(get_db)):
    receita = db.query(Receita).filter(Receita.id == receita_id).first()
    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    custo_total, custo_unitario = _calcular_custo_receita(receita)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=16,
        spaceAfter=8
    )
    normal = styles["Normal"]

    story = []

    story.append(Paragraph("PRECIFICA — Ficha Técnica", title_style))
    story.append(Paragraph(receita.nome, subtitle_style))

    # Info geral
    info_data = [
        ["Categoria", receita.categoria or "—"],
        ["Rendimento", f"{receita.rendimento_qtd} {receita.rendimento_unidade}"],
        ["Tempo de preparo", f"{receita.tempo_preparo_min} min"],
        ["Custo total (insumos)", f"R$ {custo_total:.2f}"],
        ["Custo unitário", f"R$ {custo_unitario:.2f}"],
    ]
    info_table = Table(info_data, colWidths=[6 * cm, 10 * cm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
    ]))
    story.append(info_table)

    if receita.observacao:
        story.append(Paragraph("Observação", section_style))
        story.append(Paragraph(receita.observacao, normal))

    # Ingredientes
    story.append(Paragraph("Ingredientes", section_style))

    header = ["Ingrediente", "Quantidade", "Unidade", "Custo (R$)"]
    rows = [header]
    for item in receita.itens:
        qtd_exib = item.quantidade
        un = item.unidade
        if un in ("kg", "L"):
            qtd_exib = item.quantidade / 1000
        custo = item.quantidade * item.insumo.custo_unitario
        rows.append([
            item.insumo.nome,
            f"{qtd_exib:.2f}".rstrip("0").rstrip("."),
            un,
            f"{custo:.2f}"
        ])

    ing_table = Table(rows, colWidths=[7 * cm, 3.5 * cm, 3 * cm, 3.5 * cm])
    ing_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a1a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f5f2")]),
    ]))
    story.append(ing_table)

    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        f"<i>Gerado pelo PRECIFICA · Custo total: R$ {custo_total:.2f} · "
        f"Custo unitário: R$ {custo_unitario:.2f}</i>",
        ParagraphStyle("Footer", parent=normal, fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f"ficha_{receita.nome.replace(' ', '_').lower()}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
