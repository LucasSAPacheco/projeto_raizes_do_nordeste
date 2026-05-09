from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import PerfilUsuario
from app.api.deps import exigir_perfil
from app.application.produto_service import (
    listar_produtos, buscar_produto, criar_produto,
    atualizar_produto, remover_produto
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])


# ── Schemas ─────────────────────────────────────────────

class ProdutoRequest(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: float
    categoria: str


class ProdutoUpdateRequest(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[float] = None
    categoria: Optional[str] = None
    disponivel: Optional[bool] = None


class ProdutoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    preco: float
    categoria: str
    disponivel: bool

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────

@router.get("", response_model=list[ProdutoResponse], summary="Listar produtos")
def listar(
    categoria: Optional[str] = None,
    apenas_disponiveis: bool = True,
    db: Session = Depends(get_db)
):
    """Lista produtos do cardápio. Filtra por categoria e/ou disponibilidade."""
    return listar_produtos(db, categoria, apenas_disponiveis)


@router.get("/{produto_id}", response_model=ProdutoResponse, summary="Buscar produto")
def buscar(produto_id: int, db: Session = Depends(get_db)):
    """Retorna os dados de um produto pelo ID."""
    return buscar_produto(db, produto_id)


@router.post("", response_model=ProdutoResponse, status_code=201,
             summary="Criar produto",
             dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))])
def criar(body: ProdutoRequest, db: Session = Depends(get_db)):
    """Cadastra um novo produto no cardápio. Apenas ADMIN ou GERENTE."""
    return criar_produto(db, body.nome, body.descricao, body.preco, body.categoria)


@router.patch("/{produto_id}", response_model=ProdutoResponse, summary="Atualizar produto",
              dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))])
def atualizar(produto_id: int, body: ProdutoUpdateRequest, db: Session = Depends(get_db)):
    """Atualiza os dados de um produto. Apenas ADMIN ou GERENTE."""
    return atualizar_produto(db, produto_id, body.model_dump(exclude_none=True))


@router.delete("/{produto_id}", response_model=ProdutoResponse, summary="Desativar produto",
               dependencies=[Depends(exigir_perfil(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE))])
def remover(produto_id: int, db: Session = Depends(get_db)):
    """Marca o produto como indisponível no cardápio. Apenas ADMIN ou GERENTE."""
    return remover_produto(db, produto_id)
