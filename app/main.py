import os
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .database import engine, Base, SessionLocal
from .models import Configuracao
from .routers import insumos, receitas, calculadora, config
from .auth import APP_PASSWORD, SESSION_SECRET, is_authenticated

# Cria as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PRECIFICA", version="0.1.0")

# Static e Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Routers
app.include_router(insumos.router)
app.include_router(receitas.router)
app.include_router(calculadora.router)
app.include_router(config.router)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Libera estáticos, login e health
    if (
        path.startswith("/static")
        or path in ("/login", "/health")
        or path.startswith("/docs")
        or path.startswith("/openapi")
    ):
        return await call_next(request)

    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)


# SessionMiddleware DEVE ser o último add_middleware
# (fica por fora e inicializa request.session antes do auth)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    max_age=60 * 60 * 24 * 7,  # 7 dias
    same_site="lax",
)


@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        cfg = db.query(Configuracao).first()
        if not cfg:
            cfg = Configuracao()
            db.add(cfg)
            db.commit()
    finally:
        db.close()


@app.get("/login")
def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/receitas", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "erro": None})


@app.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if password == APP_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/receitas", status_code=303)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "erro": "Senha incorreta. Tente novamente."
    })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
def home(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/receitas", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}
