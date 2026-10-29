"""Validaciones de los formularios que recibe la API."""

from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Formulario(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, allow_inf_nan=False)


class Login(BaseModel):
    correo: str = Field(min_length=3, max_length=120)
    contrasena: str = Field(min_length=1, max_length=128)


class UsuarioDatos(Formulario):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str = Field(min_length=5, max_length=120)
    telefono: str = Field(default="", max_length=20)
    id_rol: int = Field(gt=0)
    activo: Literal[0, 1] = 1

    @field_validator("nombre", "correo", "telefono", mode="before")
    @classmethod
    def limpiar_texto(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("correo")
    @classmethod
    def correo_valido(cls, value):
        import re

        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Escribe un correo válido")
        return value.lower()


class UsuarioCrear(UsuarioDatos):
    model_config = ConfigDict(str_strip_whitespace=False)
    contrasena: str = Field(min_length=8, max_length=128)

    @field_validator("contrasena")
    @classmethod
    def conservar_contrasena(cls, value):
        if not value.strip():
            raise ValueError("La contraseña no puede estar vacía")
        return value


class CategoriaDatos(Formulario):
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str = Field(default="", max_length=200)
    estado: Literal["ACTIVO", "INACTIVO"] = "ACTIVO"


class ProductoDatos(Formulario):
    id_categoria: int = Field(gt=0)
    codigo: str = Field(min_length=2, max_length=30)
    nombre: str = Field(min_length=2, max_length=120)
    descripcion: str = Field(default="", max_length=250)
    precio_base: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    precio_reventa_sugerido: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock_actual: int = Field(ge=0, le=1000000)
    stock_minimo: int = Field(default=5, ge=0, le=1000000)
    estado: Literal["ACTIVO", "INACTIVO"] = "ACTIVO"


class ItemPedido(Formulario):
    id_producto: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=1000000)


class PedidoDatos(Formulario):
    id_revendedor: int | None = Field(default=None, gt=0)
    observaciones: str = Field(default="", max_length=250)
    items: list[ItemPedido] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def sin_repetidos(self):
        ids = [item.id_producto for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada producto debe aparecer una sola vez")
        return self


class PagoDatos(Formulario):
    id_pedido: int = Field(gt=0)
    monto: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    metodo_pago: Literal["EFECTIVO", "TRANSFERENCIA", "TARJETA"]
    referencia_transaccion: str = Field(default="", max_length=60)
