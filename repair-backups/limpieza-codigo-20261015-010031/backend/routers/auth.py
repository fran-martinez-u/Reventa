import secrets
import time
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Usuario, Rol
from backend.schemas.schemas import Login, UsuarioCrear, UsuarioDatos
from backend.services.auth import (
    SESIONES, hash_password, verify_password, usuario_actual, administrador, personal, datos_usuario,
)

router = APIRouter(prefix='/api/auth', tags=['Usuarios y acceso'])


@router.post('/login')
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(func.lower(Usuario.correo) == data.correo.strip().lower()).first()
    if not user or not verify_password(data.contrasena, user.password_hash):
        raise HTTPException(401, 'Correo o contraseña incorrectos')
    if not user.activo:
        raise HTTPException(403, 'La cuenta está desactivada')
    if not user.password_hash.startswith('pbkdf2_sha256$'):
        user.password_hash = hash_password(data.contrasena)
        db.commit()
    now = time.time()
    for old in [token for token, session in SESIONES.items() if session['vence'] <= now]:
        SESIONES.pop(old, None)
    token = secrets.token_urlsafe(32)
    SESIONES[token] = {'id_usuario': user.id_usuario, 'vence': now + 8 * 3600}
    return {'access_token': token, 'token_type': 'bearer', 'usuario': datos_usuario(user)}


@router.post('/logout')
def logout(authorization: str | None = Header(None), user=Depends(usuario_actual)):
    SESIONES.pop(authorization[7:], None)
    return {'mensaje': 'Sesión cerrada'}


@router.get('/me')
def me(user=Depends(usuario_actual)):
    return datos_usuario(user)


@router.get('/roles')
def roles(db: Session = Depends(get_db), user=Depends(administrador)):
    return [{'id_rol': r.id_rol, 'nombre': r.nombre} for r in db.query(Rol).order_by(Rol.id_rol)]


@router.get('/revendedores')
def revendedores(db: Session = Depends(get_db), user=Depends(personal)):
    rows = db.query(Usuario).join(Rol).filter(Rol.nombre == 'REVENDEDOR', Usuario.activo == 1)
    return [{'id_usuario': u.id_usuario, 'nombre': u.nombre} for u in rows.order_by(Usuario.nombre)]


@router.get('/usuarios')
def usuarios(q: str = Query(default='', max_length=100), db: Session = Depends(get_db), user=Depends(administrador)):
    query = db.query(Usuario)
    if q:
        query = query.filter(Usuario.nombre.ilike(f'%{q}%') | Usuario.correo.ilike(f'%{q}%'))
    return [datos_usuario(u) for u in query.order_by(Usuario.id_usuario)]


@router.get('/usuarios/{id_usuario}')
def consultar(id_usuario: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, 'Usuario no encontrado')
    return datos_usuario(row)


@router.post('/usuarios', status_code=201)
def crear(data: UsuarioCrear, db: Session = Depends(get_db), user=Depends(administrador)):
    if not db.get(Rol, data.id_rol):
        raise HTTPException(400, 'Selecciona un rol válido')
    values = data.model_dump(exclude={'contrasena'})
    row = Usuario(**values, password_hash=hash_password(data.contrasena))
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos_usuario(row)


@router.put('/usuarios/{id_usuario}')
def actualizar(id_usuario: int, data: UsuarioDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, 'Usuario no encontrado')
    role = db.get(Rol, data.id_rol)
    if not role:
        raise HTTPException(400, 'Selecciona un rol válido')
    if row.id_usuario == user.id_usuario and (not data.activo or role.nombre != 'ADMIN'):
        raise HTTPException(400, 'No puedes quitarte el acceso de administrador')
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return datos_usuario(row)


@router.delete('/usuarios/{id_usuario}')
def desactivar(id_usuario: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, 'Usuario no encontrado')
    if row.id_usuario == user.id_usuario:
        raise HTTPException(400, 'No puedes desactivar tu propia cuenta')
    row.activo = 0
    db.commit()
    return {'mensaje': 'Usuario desactivado'}
