from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.models import PerfilUsuario
from app.application.auth_service import cadastrar_usuario, login
from app.api.deps import get_usuario_atual
from app.domain.models import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


# ── Schemas de entrada e saída ──────────────────────────

class CadastroRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: PerfilUsuario = PerfilUsuario.CLIENTE
    consentimento_lgpd: bool


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    ativo: bool

    class Config:
        from_attributes = True


# ── Endpoints ───────────────────────────────────────────

@router.post("/cadastro", response_model=UsuarioResponse, status_code=201,
             summary="Cadastrar novo usuário")
def cadastro(body: CadastroRequest, db: Session = Depends(get_db)):
    """
    Cria uma nova conta. O campo **consentimento_lgpd** deve ser `true`
    para confirmar que o usuário aceita o uso dos seus dados (exigência da LGPD).
    """
    return cadastrar_usuario(
        db=db,
        nome=body.nome,
        email=body.email,
        senha=body.senha,
        perfil=body.perfil,
        consentimento_lgpd=body.consentimento_lgpd,
    )


@router.post("/login", response_model=TokenResponse, summary="Fazer login")
def fazer_login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica o usuário e retorna um token JWT.
    Use o token no cabeçalho: `Authorization: Bearer <token>`
    """
    return login(db=db, email=body.email, senha=body.senha)


@router.get("/me", response_model=UsuarioResponse, summary="Ver meu perfil")
def meu_perfil(usuario_atual: Usuario = Depends(get_usuario_atual)):
    """Retorna os dados do usuário autenticado pelo token."""
    return usuario_atual
