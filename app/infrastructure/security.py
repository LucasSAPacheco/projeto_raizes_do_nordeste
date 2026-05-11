from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.infrastructure.config import settings

criptografia = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return criptografia.hash(senha)


def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    return criptografia.verify(senha_pura, senha_hash)


def criar_token(dados: dict, expira_em: Optional[int] = None) -> str:
    payload = dados.copy()
    tempo = expira_em or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    validade = datetime.utcnow() + timedelta(minutes=tempo)
    payload.update({"exp": validade})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decodificar_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
