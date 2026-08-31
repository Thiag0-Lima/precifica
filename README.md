# PRECIFICA

Sistema interno de precificação e ficha técnica para confeitarias, padarias e pequenos produtores de alimentos.

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: HTML + CSS puro + JavaScript vanilla (Jinja2 templates)

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.10 ou superior
- VS Code (recomendado)

### 2. Setup

```bash
# Entre na pasta do projeto
cd precifica

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Rodar o servidor

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abra no navegador: **http://127.0.0.1:8000**

### 4. Ordem de uso recomendada

1. **Config** → ajuste custos invisíveis, taxa horária e margem mínima
2. **Ingredientes** → cadastre os insumos
3. **Receitas** → monte as fichas técnicas
4. **Calculadora** → escale e simule preços

## Estrutura

```
precifica/
├── app/
│   ├── main.py              # Entry point
│   ├── database.py          # Conexão SQLite
│   ├── models.py            # Tabelas
│   ├── schemas.py           # Pydantic
│   ├── routers/             # Rotas por módulo
│   ├── static/              # CSS + JS
│   └── templates/           # HTML
├── requirements.txt
└── README.md
```

## Observações

- O banco `precifica.db` é criado automaticamente na primeira execução.
- Todas as conversões de unidade (kg↔g, L↔ml) são feitas automaticamente.
- O sistema é single-user e pensado para uso interno.
