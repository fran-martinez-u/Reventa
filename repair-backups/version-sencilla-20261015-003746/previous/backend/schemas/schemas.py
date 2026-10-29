from pydantic import BaseModel
from typing import Optional

# === SCHEMAS PARA CATEGORÍAS ===
class CategoriaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int

    class Config:
        from_attributes = True

# === SCHEMAS PARA PRODUCTOS ===
class ProductoBase(BaseModel):
    nombre: str
    precio: float
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoResponse(ProductoBase):
    id: int
    categoria: Optional[CategoriaResponse] = None

    class Config:
        from_attributes = True