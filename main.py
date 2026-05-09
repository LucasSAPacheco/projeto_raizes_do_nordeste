from fastapi import FastAPI
from app.api.auth_router import router as auth_router
from app.api.unidade_router import router as unidade_router

app = FastAPI(
    title='Raízes do Nordeste API',
    description='API de controle da lanchonete Raizes do Nordeste',
    version='1.0.0'
)

app.include_router(auth_router)
app.include_router(unidade_router)


@app.get("/health", tags=["Saúde"])
def health():
    return {"status": "ok", "message": "Api criada pelo Lucas está saudável, igual nossos pratos!"}
