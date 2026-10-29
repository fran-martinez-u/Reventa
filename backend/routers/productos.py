"""CRUD y búsqueda de productos del catálogo."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Producto, Categoria
from backend.schemas.schemas import ProductoDatos
from backend.services.auth import usuario_actual, administrador
from backend.services.catalogo import buscar, datos_producto as datos

router = APIRouter(prefix="/api", tags=["Productos"])


@router.get("/productos")
def productos(
    q: str = Query(default="", max_length=100),
    id_categoria: int | None = Query(default=None, gt=0),
    estado: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(usuario_actual),
):
    query = db.query(Producto)
    if q:
        query = query.filter(
            Producto.nombre.ilike(f"%{q}%") | Producto.codigo.ilike(f"%{q}%")
        )
    if id_categoria:
        query = query.filter(Producto.id_categoria == id_categoria)
    if estado:
        query = query.filter(Producto.estado == estado)
    return [datos(row) for row in query.order_by(Producto.id_producto)]


@router.get("/productos/{id}")
def producto(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos(buscar(db, Producto, id))


def categoria_activa(db, id):
    row = db.get(Categoria, id)
    if not row or row.estado != "ACTIVO":
        raise HTTPException(400, "Selecciona una categoría activa")


@router.post("/productos", status_code=201)
def crear_producto(
    data: ProductoDatos, db: Session = Depends(get_db), user=Depends(administrador)
):
    categoria_activa(db, data.id_categoria)
    row = Producto(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos(row)


@router.put("/productos/{id}")
def editar_producto(
    id: int,
    data: ProductoDatos,
    db: Session = Depends(get_db),
    user=Depends(administrador),
):
    row = (
        db.query(Producto).filter(Producto.id_producto == id).with_for_update().first()
    )
    if not row:
        raise HTTPException(404, "Producto no encontrado")
    if data.id_categoria != row.id_categoria:
        categoria_activa(db, data.id_categoria)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return datos(row)


@router.delete("/productos/{id}")
def eliminar_producto(
    id: int, db: Session = Depends(get_db), user=Depends(administrador)
):
    row = buscar(db, Producto, id)
    row.estado = "INACTIVO"
    db.commit()
    return {"mensaje": "Producto desactivado"}
