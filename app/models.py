from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Insumo(Base):
    __tablename__ = "insumos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    quantidade_embalagem = Column(Float, nullable=False)  # ex: 1000
    unidade = Column(String(10), nullable=False)          # g, kg, ml, L, un
    preco = Column(Float, nullable=False)
    fornecedor = Column(String(120), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    @property
    def custo_unitario(self):
        """Retorna o custo por unidade base (g, ml ou un)"""
        if self.unidade in ("kg", "L"):
            return self.preco / (self.quantidade_embalagem * 1000)
        return self.preco / self.quantidade_embalagem

    @property
    def unidade_base(self):
        if self.unidade == "kg":
            return "g"
        if self.unidade == "L":
            return "ml"
        return self.unidade


class Receita(Base):
    __tablename__ = "receitas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    categoria = Column(String(50), nullable=True)
    rendimento_qtd = Column(Float, nullable=False)        # ex: 12
    rendimento_unidade = Column(String(20), nullable=False)  # fatias, un, g...
    tempo_preparo_min = Column(Integer, default=0)
    observacao = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    itens = relationship("ReceitaItem", back_populates="receita", cascade="all, delete-orphan")


class ReceitaItem(Base):
    __tablename__ = "receita_itens"

    id = Column(Integer, primary_key=True, index=True)
    receita_id = Column(Integer, ForeignKey("receitas.id"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("insumos.id"), nullable=False)
    quantidade = Column(Float, nullable=False)            # sempre na unidade base (g/ml/un)
    unidade = Column(String(10), nullable=False)          # unidade que o usuário digitou

    receita = relationship("Receita", back_populates="itens")
    insumo = relationship("Insumo")


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    custos_invisiveis_pct = Column(Float, default=12.0)
    taxa_horaria = Column(Float, default=15.0)
    margem_minima_alerta = Column(Float, default=40.0)
    embalagem_padrao = Column(Float, default=0.80)
    taxa_cartao_pct = Column(Float, default=5.0)
