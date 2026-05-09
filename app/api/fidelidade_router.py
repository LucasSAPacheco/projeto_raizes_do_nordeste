from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import Usuario
from app.api.deps import get_usuario_atual
from app.application.fidelidade_service import (
    consultar_saldo, ganhar_pontos, resgatar_pontos, historico_pontos
)

router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])


# ── Schemas ─────────────────────────────────────────────

class ResgateRequest(BaseModel):
    quantidade: int


class GanhoRequest(BaseModel):
    pedido_id: int


class SaldoResponse(BaseModel):
    usuario_id: int
    saldo: int

    class Config:
        from_attributes = True


class HistoricoResponse(BaseModel):
    tipo: str
    quantidade: int
    pedido_id: int | None

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────

@router.get("/saldo", response_model=SaldoResponse, summary="Consultar saldo de pontos")
def saldo(usuario_atual: Usuario = Depends(get_usuario_atual),
          db: Session = Depends(get_db)):
    """Retorna o saldo atual de pontos do cliente logado."""
    return consultar_saldo(db, usuario_atual.id)


@router.post("/ganhar", response_model=SaldoResponse, summary="Ganhar pontos por pedido")
def ganhar(body: GanhoRequest,
           usuario_atual: Usuario = Depends(get_usuario_atual),
           db: Session = Depends(get_db)):
    """
    Credita pontos ao cliente com base no valor do pedido pago.
    Regra: 1 ponto a cada R$1,00 gasto.
    """
    return ganhar_pontos(db, usuario_atual.id, body.pedido_id)


@router.post("/resgatar", response_model=SaldoResponse, summary="Resgatar pontos")
def resgatar(body: ResgateRequest,
             usuario_atual: Usuario = Depends(get_usuario_atual),
             db: Session = Depends(get_db)):
    """Desconta pontos do saldo do cliente para resgate."""
    return resgatar_pontos(db, usuario_atual.id, body.quantidade)


@router.get("/historico", response_model=list[HistoricoResponse],
            summary="Histórico de pontos")
def historico(usuario_atual: Usuario = Depends(get_usuario_atual),
              db: Session = Depends(get_db)):
    """Retorna o histórico completo de ganhos e resgates do cliente."""
    return historico_pontos(db, usuario_atual.id)
