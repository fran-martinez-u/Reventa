"""Autenticación sencilla con sesiones de ocho horas en el servidor."""
import hashlib
import hmac
import secrets
import time
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Usuario

SESIONES = {}


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()
    return f'pbkdf2_sha256${salt}${digest}'


def verify_password(password, stored):
    if stored.startswith('pbkdf2_sha256$'):
        _, salt, digest = stored.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()
    else:
        # Compatibilidad con las cuentas existentes; se actualizan al iniciar sesión.
        digest = stored
        actual = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(actual, digest)


def usuario_actual(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    token = authorization[7:] if authorization and authorization.startswith('Bearer ') else ''
    session = SESIONES.get(token)
    if not session or session['vence'] <= time.time():
        SESIONES.pop(token, None)
        raise HTTPException(401, 'Inicia sesión para continuar')
    user = db.get(Usuario, session['id_usuario'])
    if not user or not user.activo:
        raise HTTPException(401, 'La cuenta no está disponible')
    return user


def administrador(user=Depends(usuario_actual)):
    if user.rol.nombre != 'ADMIN':
        raise HTTPException(403, 'Esta acción requiere una cuenta de administrador')
    return user


def personal(user=Depends(usuario_actual)):
    if user.rol.nombre not in ('ADMIN', 'VENDEDOR'):
        raise HTTPException(403, 'Esta acción requiere administrador o vendedor')
    return user


def datos_usuario(user):
    return {'id_usuario': user.id_usuario, 'nombre': user.nombre, 'correo': user.correo,
            'telefono': user.telefono or '', 'id_rol': user.id_rol,
            'rol': user.rol.nombre, 'activo': user.activo}
