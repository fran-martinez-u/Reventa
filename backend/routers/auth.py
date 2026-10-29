"""Inicio de sesión, cierre de sesión y consulta de la cuenta actual."""

import secrets
import time
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Usuario
from backend.schemas.schemas import Login
from backend.services.auth import (
    SESIONES,
    hash_password,
    verify_password,
    usuario_actual,
    datos_usuario,
)

router = APIRouter(prefix="/api/auth", tags=["Acceso"])


@router.post("/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = (
        db.query(Usuario)
        .filter(func.lower(Usuario.correo) == data.correo.strip().lower())
        .first()
    )
    if not user or not verify_password(data.contrasena, user.password_hash):
        raise HTTPException(401, "Correo o contraseña incorrectos")
    if not user.activo:
        raise HTTPException(403, "La cuenta está desactivada")
    if not user.password_hash.startswith("pbkdf2_sha256$"):
        user.password_hash = hash_password(data.contrasena)
        db.commit()
    now = time.time()
    for old in [
        token for token, session in SESIONES.items() if session["vence"] <= now
    ]:
        SESIONES.pop(old, None)
    token = secrets.token_urlsafe(32)
    SESIONES[token] = {"id_usuario": user.id_usuario, "vence": now + 8 * 3600}
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": datos_usuario(user),
    }


@router.post("/logout")
def logout(authorization: str | None = Header(None), user=Depends(usuario_actual)):
    SESIONES.pop(authorization[7:], None)
    return {"mensaje": "Sesión cerrada"}


@router.get("/me")
def me(user=Depends(usuario_actual)):
    return datos_usuario(user)
