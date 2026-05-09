from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.infrastructure.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """Transforma a senha em um hash seguro antes de salvar no banco."""
    return pwd_context.hash(senha)


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    """Confere se a senha digitada bate com o hash salvo no banco."""
    return pwd_context.verify(senha_pura, senha_hash)


def criar_token(dados: dict, expira_em: Optional[int] = None) -> str:
    """Gera um token JWT com os dados do usuário e um prazo de validade."""
    payload = dados.copy()
    minutos = expira_em or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expiracao = datetime.utcnow() + timedelta(minutes=minutos)
    payload.update({"exp": expiracao})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    """Lê e valida um token JWT. Retorna None se for inválido ou expirado."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
