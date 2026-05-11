from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import PerfilUsuario, TipoMovimentacaoEstoque
from app.api.deps import exigir_perfil
from app.application.estoque_service import (
    listar_estoque_por_unidade, buscar_estoque, movimentar_estoque
)

router = APIRouter(prefix="/estoque", tags=["Estoque"])
class MovimentacaoRequest(BaseModel):
    unidade_id: int
    produto_id: int
    tipo: TipoMovimentacaoEstoque
    quantidade: int
    observacao: Optional[str] = None

class EstoqueResponse(BaseModel):
    id: int
    unidade_id: int
    produto_id: int
    quantidade: int
    class Config:
        from_attributes = True

@router.get("/unidades/{unidade_id}", response_model=list[EstoqueResponse],
            summary="Consultar estoque da unidade",
            dependencies=[Depends(exigir_perfil(
                PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE
            ))])
def listar(unidade_id: int, db: Session = Depends(get_db)):
    return listar_estoque_por_unidade(db, unidade_id)

@router.get("/unidades/{unidade_id}/produtos/{produto_id}",
            response_model=EstoqueResponse,
            summary="Consultar saldo de um produto na unidade",
            dependencies=[Depends(exigir_perfil(
                PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE
            ))])
def consultar(unidade_id: int, produto_id: int, db: Session = Depends(get_db)):
    return buscar_estoque(db, unidade_id, produto_id)


@router.post("/movimentar", response_model=EstoqueResponse,
             summary="Entrada ou saída de estoque",
             dependencies=[Depends(exigir_perfil(
                 PerfilUsuario.ADMIN, PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE
             ))])
def movimentar(body: MovimentacaoRequest, db: Session = Depends(get_db)):
    return movimentar_estoque(
        db, body.unidade_id, body.produto_id,
        body.tipo, body.quantidade, body.observacao
    )
