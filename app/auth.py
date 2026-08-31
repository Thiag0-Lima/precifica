import os
from fastapi import Request

# Senha definida por variável de ambiente (padrão só para desenvolvimento local)
APP_PASSWORD = os.getenv("APP_PASSWORD", "precifica123")
SESSION_SECRET = os.getenv("SESSION_SECRET", "troque-esta-chave-em-producao-xyz789")


def is_authenticated(request: Request) -> bool:
    try:
        return request.session.get("authenticated") is True
    except Exception:
        return False
