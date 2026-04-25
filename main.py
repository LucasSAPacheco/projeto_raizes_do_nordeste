from fastapi import FastAPI

app = FastAPI(
    title='Raízes do Nordeste API',
    description='API de controle da lanchonete Raizes do Nordeste',
    version='1.0.0'
)

@app.get("/health")
def health():
    return {"Status": "Ok!", "message": "Api criada pelo Lucas está saudável, igual nossos pratos!"}