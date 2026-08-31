from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== Insumo ==========
class InsumoBase(BaseModel):
    nome: str
    quantidade_embalagem: float = Field(gt=0)
    unidade: str
    preco: float = Field(ge=0)
    fornecedor: Optional[str] = None


class InsumoCreate(InsumoBase):
    pass


class InsumoUpdate(InsumoBase):
    pass


class InsumoOut(InsumoBase):
    id: int
    custo_unitario: float
    unidade_base: str
    criado_em: datetime

    class Config:
        from_attributes = True


# ========== Receita Item ==========
class ReceitaItemBase(BaseModel):
    insumo_id: int
    quantidade: float = Field(gt=0)
    unidade: str


class ReceitaItemCreate(ReceitaItemBase):
    pass


class ReceitaItemOut(ReceitaItemBase):
    id: int
    insumo_nome: Optional[str] = None
    custo: Optional[float] = None

    class Config:
        from_attributes = True


# ========== Receita ==========
class ReceitaBase(BaseModel):
    nome: str
    categoria: Optional[str] = None
    rendimento_qtd: float = Field(gt=0)
    rendimento_unidade: str
    tempo_preparo_min: int = 0
    observacao: Optional[str] = None


class ReceitaCreate(ReceitaBase):
    itens: List[ReceitaItemCreate] = []


class ReceitaUpdate(ReceitaBase):
    itens: List[ReceitaItemCreate] = []


class ReceitaOut(ReceitaBase):
    id: int
    criado_em: datetime
    itens: List[ReceitaItemOut] = []
    custo_total: Optional[float] = None
    custo_unitario: Optional[float] = None

    class Config:
        from_attributes = True


# ========== Configuração ==========
class ConfiguracaoBase(BaseModel):
    custos_invisiveis_pct: float = 12.0
    taxa_horaria: float = 15.0
    margem_minima_alerta: float = 40.0
    embalagem_padrao: float = 0.80
    taxa_cartao_pct: float = 5.0


class ConfiguracaoOut(ConfiguracaoBase):
    id: int

    class Config:
        from_attributes = True


# ========== Calculadora ==========
class CalculadoraRequest(BaseModel):
    receita_id: int
    rendimento_desejado: float = Field(gt=0)
    rendimento_unidade: Optional[str] = None  # se None, usa a da receita
    margem_desejada: Optional[float] = None
    preco_alvo: Optional[float] = None


class CalculadoraResponse(BaseModel):
    receita_nome: str
    rendimento_desejado: float
    rendimento_unidade: str
    fator: float
    itens: List[dict]
    custo_insumos: float
    custo_invisiveis: float
    custo_mao_obra: float
    custo_embalagem: float
    custo_total: float
    custo_unitario: float
    preco_sugerido: Optional[float] = None
    lucro: Optional[float] = None
    margem_real: Optional[float] = None
