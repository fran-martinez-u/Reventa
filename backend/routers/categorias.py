"""CRUD de categorías. La eliminación cambia el estado a INACTIVO."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Categoria
from backend.schemas.schemas import CategoriaDatos
from backend.services.auth import usuario_actual, administrador
from backend.services.catalogo import buscar, datos_categoria as datos

router = APIRouter(prefix="/api", tags=["Categorías"])


@router.get("/categorias")
def categorias(
    q: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
    user=Depends(usuario_actual),
):
    query = db.query(Categoria)
    if q:
        query = query.filter(Categoria.nombre.ilike(f"%{q}%"))
    return [datos(row) for row in query.order_by(Categoria.nombre)]


@router.get("/categorias/{id}")
def categoria(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos(buscar(db, Categoria, id))


@router.post("/categorias", status_code=201)
def crear_categoria(
    data: CategoriaDatos, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = Categoria(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos(row)


@router.put("/categorias/{id}")
def editar_categoria(
    id: int,
    data: CategoriaDatos,
    db: Session = Depends(get_db),
    user=Depends(administrador),
):
    row = buscar(db, Categoria, id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return datos(row)


@router.delete("/categorias/{id}")
def eliminar_categoria(
    id: int, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = buscar(db, Categoria, id)
    row.estado = "INACTIVO"
    db.commit()
    return {"mensaje": "Categoría desactivada"}
