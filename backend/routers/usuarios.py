"""Consulta, creación, edición y desactivación de usuarios."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Usuario, Rol
from backend.schemas.schemas import UsuarioCrear, UsuarioDatos
from backend.services.auth import administrador, personal, datos_usuario, hash_password

router = APIRouter(prefix="/api/auth", tags=["Usuarios"])


@router.get("/roles")
def roles(db: Session = Depends(get_db), user=Depends(administrador)):
    return [
        {"id_rol": r.id_rol, "nombre": r.nombre}
        for r in db.query(Rol).order_by(Rol.id_rol)
    ]


@router.get("/revendedores")
def revendedores(db: Session = Depends(get_db), user=Depends(personal)):
    rows = (
        db.query(Usuario)
        .join(Rol)
        .filter(Rol.nombre == "REVENDEDOR", Usuario.activo == 1)
    )
    return [
        {"id_usuario": u.id_usuario, "nombre": u.nombre}
        for u in rows.order_by(Usuario.nombre)
    ]


@router.get("/usuarios")
def usuarios(
    q: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
    user=Depends(administrador),
):
    query = db.query(Usuario)
    if q:
        query = query.filter(
            Usuario.nombre.ilike(f"%{q}%") | Usuario.correo.ilike(f"%{q}%")
        )
    return [datos_usuario(u) for u in query.order_by(Usuario.id_usuario)]


@router.get("/usuarios/{id_usuario}")
def consultar(
    id_usuario: int, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, "Usuario no encontrado")
    return datos_usuario(row)


@router.post("/usuarios", status_code=201)
def crear(
    data: UsuarioCrear, db: Session = Depends(get_db), user=Depends(administrador)
):
    if not db.get(Rol, data.id_rol):
        raise HTTPException(400, "Selecciona un rol válido")
    values = data.model_dump(exclude={"contrasena"})
    row = Usuario(**values, password_hash=hash_password(data.contrasena))
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos_usuario(row)


@router.put("/usuarios/{id_usuario}")
def actualizar(
    id_usuario: int,
    data: UsuarioDatos,
    db: Session = Depends(get_db),
    user=Depends(administrador),
):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, "Usuario no encontrado")
    role = db.get(Rol, data.id_rol)
    if not role:
        raise HTTPException(400, "Selecciona un rol válido")
    if row.id_usuario == user.id_usuario and (
        not data.activo or role.nombre != "ADMIN"
    ):
        raise HTTPException(400, "No puedes quitarte el acceso de administrador")
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return datos_usuario(row)


@router.delete("/usuarios/{id_usuario}")
def desactivar(
    id_usuario: int, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = db.get(Usuario, id_usuario)
    if not row:
        raise HTTPException(404, "Usuario no encontrado")
    if row.id_usuario == user.id_usuario:
        raise HTTPException(400, "No puedes desactivar tu propia cuenta")
    row.activo = 0
    db.commit()
    return {"mensaje": "Usuario desactivado"}
