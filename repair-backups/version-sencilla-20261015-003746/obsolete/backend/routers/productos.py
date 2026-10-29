from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Producto
from backend.schemas.schemas import ProductoCreate, ProductoResponse

router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

@router.post("/", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    nuevo_producto = Producto(**producto.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@router.get("/", response_model=list[ProductoResponse])
def obtener_productos(db: Session = Depends(get_db)):
    return db.query(Producto).all()
@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(producto_id: int, producto_actualizado: ProductoCreate, db: Session = Depends(get_db)):
    # Buscar el producto en la base de datos
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Actualizar los campos
    producto.nombre = producto_actualizado.nombre
    producto.precio = producto_actualizado.precio
    producto.descripcion = producto_actualizado.descripcion
    
    db.commit()
    db.refresh(producto)
    return producto

@router.delete("/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    # Buscar el producto en la base de datos
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Eliminarlo
    db.delete(producto)
    db.commit()
    return {"mensaje": "Producto eliminado exitosamente"}
