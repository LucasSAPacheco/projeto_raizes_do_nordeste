import logging
from fastapi import FastAPI
from app.api.auth_router import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from app.api.unidade_router import router as unidade_router
from app.api.produto_router import router as produto_router
from app.api.estoque_router import router as estoque_router
from app.api.pedido_router import router as pedido_router
from app.api.pagamento_router import router as pagamento_router
from app.api.fidelidade_router import router as fidelidade_router

app = FastAPI(
    title='Raízes do Nordeste API',
    description='API de controle da lanchonete Raizes do Nordeste',
    version='1.0.0'
)

app.include_router(auth_router)
app.include_router(unidade_router)
app.include_router(produto_router)
app.include_router(estoque_router)
app.include_router(pedido_router)
app.include_router(pagamento_router)
app.include_router(fidelidade_router)


@app.get("/health", tags=["Saúde"])
def health():
    return {"status": "ok", "message": "Api criada pelo Lucas está saudável, igual nossos pratos!"}
