from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Categoria, Producto
from backend.schemas.schemas import CategoriaDatos, ProductoDatos
from backend.services.auth import usuario_actual, administrador

router = APIRouter(prefix='/api', tags=['Catálogo'])


def datos(row):
    result = {column.name: getattr(row, column.name) for column in row.__table__.columns}
    if isinstance(row, Producto):
        result['categoria'] = row.categoria.nombre
    return result


def buscar(db, model, id):
    row = db.get(model, id)
    if not row:
        raise HTTPException(404, 'Registro no encontrado')
    return row


@router.get('/categorias')
def categorias(q: str = Query(default='', max_length=100), db: Session = Depends(get_db), user=Depends(usuario_actual)):
    query = db.query(Categoria)
    if q:
        query = query.filter(Categoria.nombre.ilike(f'%{q}%'))
    return [datos(row) for row in query.order_by(Categoria.nombre)]


@router.get('/categorias/{id}')
def categoria(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos(buscar(db, Categoria, id))


@router.post('/categorias', status_code=201)
def crear_categoria(data: CategoriaDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    row = Categoria(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos(row)


@router.put('/categorias/{id}')
def editar_categoria(id: int, data: CategoriaDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar(db, Categoria, id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return datos(row)


@router.delete('/categorias/{id}')
def eliminar_categoria(id: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar(db, Categoria, id)
    row.estado = 'INACTIVO'
    db.commit()
    return {'mensaje': 'Categoría desactivada'}


@router.get('/productos')
def productos(q: str = Query(default='', max_length=100), id_categoria: int | None = Query(default=None, gt=0),
              estado: str | None = None, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    query = db.query(Producto)
    if q:
        query = query.filter(Producto.nombre.ilike(f'%{q}%') | Producto.codigo.ilike(f'%{q}%'))
    if id_categoria:
        query = query.filter(Producto.id_categoria == id_categoria)
    if estado:
        query = query.filter(Producto.estado == estado)
    return [datos(row) for row in query.order_by(Producto.id_producto)]


@router.get('/productos/{id}')
def producto(id: int, db: Session = Depends(get_db), user=Depends(usuario_actual)):
    return datos(buscar(db, Producto, id))


def categoria_activa(db, id):
    row = db.get(Categoria, id)
    if not row or row.estado != 'ACTIVO':
        raise HTTPException(400, 'Selecciona una categoría activa')


@router.post('/productos', status_code=201)
def crear_producto(data: ProductoDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    categoria_activa(db, data.id_categoria)
    row = Producto(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return datos(row)


@router.put('/productos/{id}')
def editar_producto(id: int, data: ProductoDatos, db: Session = Depends(get_db), user=Depends(administrador)):
    row = db.query(Producto).filter(Producto.id_producto == id).with_for_update().first()
    if not row:
        raise HTTPException(404, 'Producto no encontrado')
    if data.id_categoria != row.id_categoria:
        categoria_activa(db, data.id_categoria)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return datos(row)


@router.delete('/productos/{id}')
def eliminar_producto(id: int, db: Session = Depends(get_db), user=Depends(administrador)):
    row = buscar(db, Producto, id)
    row.estado = 'INACTIVO'
    db.commit()
    return {'mensaje': 'Producto desactivado'}
