from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import PerfilUsuario, CanalPedido, StatusPedido, Usuario
from app.api.deps import get_usuario_atual, exigir_perfil
from app.application.pedido_service import (
    criar_pedido, atualizar_status, listar_pedidos, buscar_pedido
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])
class ItemPedidoRequest(BaseModel):
    produto_id: int
    quantidade: int

class PedidoRequest(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido
    itens: list[ItemPedidoRequest]
    observacao: Optional[str] = None
class AtualizarStatusRequest(BaseModel):
    status: StatusPedido

class ItemPedidoResponse(BaseModel):
    produto_id: int
    quantidade: int
    preco_unitario: float

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    unidade_id: int
    canal_pedido: CanalPedido
    status: StatusPedido
    valor_total: float
    observacao: Optional[str]
    itens: list[ItemPedidoResponse]
    class Config:
        from_attributes = True

@router.post("", response_model=PedidoResponse, status_code=201,
             summary="Criar pedido")
def criar(body: PedidoRequest,
          usuario_atual: Usuario = Depends(get_usuario_atual),
          db: Session = Depends(get_db)):
    return criar_pedido(
        db=db,
        cliente_id=usuario_atual.id,
        unidade_id=body.unidade_id,
        canal_pedido=body.canal_pedido,
        itens=[item.model_dump() for item in body.itens],
        observacao=body.observacao,
    )

@router.get("", response_model=list[PedidoResponse], summary="Listar pedidos",
            dependencies=[Depends(exigir_perfil(
                PerfilUsuario.ADMIN, PerfilUsuario.GERENTE,
                PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA
            ))])
def listar(
    unidade_id: Optional[int] = None,
    canal_pedido: Optional[CanalPedido] = None,
    status: Optional[StatusPedido] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return listar_pedidos(db, unidade_id=unidade_id, canal_pedido=canal_pedido,
                          status_pedido=status, page=page, limit=limit)

@router.get("/meus", response_model=list[PedidoResponse], summary="Meus pedidos")
def meus_pedidos(
    page: int = 1,
    limit: int = 10,
    usuario_atual: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db)
):
    return listar_pedidos(db, cliente_id=usuario_atual.id, page=page, limit=limit)


@router.get("/{pedido_id}", response_model=PedidoResponse, summary="Buscar pedido")
def buscar(pedido_id: int,
           usuario_atual: Usuario = Depends(get_usuario_atual),
           db: Session = Depends(get_db)):
    pedido = buscar_pedido(db, pedido_id)
    if (usuario_atual.perfil == PerfilUsuario.CLIENTE
            and pedido.cliente_id != usuario_atual.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para acessar este pedido.",
        )
    return pedido

@router.patch("/{pedido_id}/status", response_model=PedidoResponse,
              summary="Atualizar status do pedido",
              dependencies=[Depends(exigir_perfil(
                  PerfilUsuario.ADMIN, PerfilUsuario.GERENTE,
                  PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA
              ))])
def atualizar(pedido_id: int, body: AtualizarStatusRequest,
              usuario_atual: Usuario = Depends(get_usuario_atual),
              db: Session = Depends(get_db)):
    return atualizar_status(db, pedido_id, body.status, usuario_atual.perfil.value)
