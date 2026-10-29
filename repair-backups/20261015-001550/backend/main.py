from pathlib import Path
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, inspect

from backend.database.connection import engine, Base, get_db, SessionLocal
from backend.models.models import Rol, Usuario, Categoria, Producto, Pedido, DetallePedido, Pago

app = FastAPI(
    title="API de Revendedores (PostgreSQL - Neon)",
    description="Sistema Full Stack para gestión de catálogo, pedidos, pagos y reportes.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOKENS = {}

def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@app.on_event("startup")
def startup_event():
    insp = inspect(engine)
    if "roles" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("roles")]
        if "id_rol" not in cols:
            Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Rol).count() == 0:
            db.add_all([
                Rol(id_rol=1, nombre="ADMIN", descripcion="Administrador general"),
                Rol(id_rol=2, nombre="VENDEDOR", descripcion="Gestor comercial"),
                Rol(id_rol=3, nombre="REVENDEDOR", descripcion="Cliente mayorista")
            ])
            db.commit()

            db.add_all([
                Usuario(id_usuario=1, id_rol=1, nombre_completo="Administrador General", correo="admin@catalogo.com", telefono="3001112233", ciudad="Cali", username="admin", password_hash=hash_pw("Admin123*"), estado="ACTIVO", cupo_credito=0),
                Usuario(id_usuario=2, id_rol=2, nombre_completo="Laura Gómez", correo="laura.vendedor@catalogo.com", telefono="3002223344", ciudad="Cali", username="laura", password_hash=hash_pw("Vendedor123*"), estado="ACTIVO", cupo_credito=0),
                Usuario(id_usuario=3, id_rol=3, nombre_completo="Carlos Pérez", correo="carlos.revendedor@catalogo.com", telefono="3003334455", ciudad="Palmira", username="carlos", password_hash=hash_pw("Revendedor123*"), estado="ACTIVO", cupo_credito=1500000),
                Usuario(id_usuario=4, id_rol=3, nombre_completo="Diana Ríos", correo="diana.revendedor@catalogo.com", telefono="3004445566", ciudad="Yumbo", username="diana", password_hash=hash_pw("Revendedor123*"), estado="ACTIVO", cupo_credito=900000)
            ])
            db.commit()

            db.add_all([
                Categoria(id_categoria=1, nombre="Camisetas", descripcion="Camisetas urbanas y básicas", estado="ACTIVA"),
                Categoria(id_categoria=2, nombre="Jeans", descripcion="Jeans masculinos y femeninos", estado="ACTIVA"),
                Categoria(id_categoria=3, nombre="Chaquetas", descripcion="Chaquetas livianas y denim", estado="ACTIVA"),
                Categoria(id_categoria=4, nombre="Conjuntos", descripcion="Conjuntos deportivos", estado="ACTIVA"),
                Categoria(id_categoria=5, nombre="Calzado", descripcion="Tenis y calzado casual", estado="ACTIVA")
            ])
            db.commit()

            db.add_all([
                Producto(id_categoria=1, sku="CAM-BAS-NEG-M", nombre="Camiseta Básica Premium", talla="M", color="Negro", precio_base=28000, precio_sugerido=45000, stock_actual=45, stock_minimo=8, estado="ACTIVO"),
                Producto(id_categoria=1, sku="CAM-OVR-BLA-L", nombre="Camiseta Oversize Street", talla="L", color="Blanco", precio_base=34000, precio_sugerido=55000, stock_actual=32, stock_minimo=6, estado="ACTIVO"),
                Producto(id_categoria=2, sku="JEA-SLM-AZU-32", nombre="Jean Slim Fit Clásico", talla="32", color="Azul Oscuro", precio_base=68000, precio_sugerido=105000, stock_actual=22, stock_minimo=5, estado="ACTIVO"),
                Producto(id_categoria=3, sku="CHA-DEN-AZU-M", nombre="Chaqueta Denim Unisex", talla="M", color="Azul Medio", precio_base=95000, precio_sugerido=145000, stock_actual=10, stock_minimo=3, estado="ACTIVO"),
                Producto(id_categoria=5, sku="CAL-URB-BLA-40", nombre="Tenis Urbanos Blancos", talla="40", color="Blanco", precio_base=89000, precio_sugerido=139000, stock_actual=4, stock_minimo=5, estado="ACTIVO")
            ])
            db.commit()
    finally:
        db.close()

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = authorization.split(" ")[1]
    user_id = TOKENS.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    u = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not u:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return {
        "id_usuario": u.id_usuario,
        "username": u.username,
        "nombre_completo": u.nombre_completo,
        "correo": u.correo,
        "rol": u.rol.nombre if u.rol else "REVENDEDOR",
        "cupo_credito": u.cupo_credito,
        "ciudad": u.ciudad,
        "estado": u.estado
    }

class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter((Usuario.username == req.username) | (Usuario.correo == req.username)).first()
    if not u or (u.password_hash != hash_pw(req.password) and u.password_hash != req.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if u.estado != "ACTIVO":
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    token = secrets.token_hex(24)
    TOKENS[token] = u.id_usuario
    user_data = {
        "id_usuario": u.id_usuario, "username": u.username, "nombre_completo": u.nombre_completo,
        "correo": u.correo, "rol": u.rol.nombre if u.rol else "REVENDEDOR",
        "cupo_credito": u.cupo_credito, "ciudad": u.ciudad, "estado": u.estado
    }
    return {"access_token": token, "token_type": "bearer", "user": user_data}

@app.get("/api/auth/me")
def me(user=Depends(get_current_user)):
    return user

@app.get("/api/auth/roles")
def listar_roles(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{"id_rol": r.id_rol, "nombre": r.nombre, "descripcion": r.descripcion} for r in db.query(Rol).all()]

@app.get("/api/auth/usuarios")
def listar_usuarios(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{
        "id_usuario": u.id_usuario, "id_rol": u.id_rol, "rol": u.rol.nombre if u.rol else "",
        "nombre_completo": u.nombre_completo, "correo": u.correo, "telefono": u.telefono,
        "ciudad": u.ciudad, "username": u.username, "estado": u.estado, "cupo_credito": u.cupo_credito
    } for u in db.query(Usuario).all()]

class UsuarioCreate(BaseModel):
    id_rol: int
    nombre_completo: str
    correo: str
    telefono: Optional[str] = ""
    ciudad: Optional[str] = ""
    username: str
    password: str
    estado: str = "ACTIVO"
    cupo_credito: float = 0.0

@app.post("/api/auth/usuarios", status_code=201)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    nuevo = Usuario(
        id_rol=payload.id_rol, nombre_completo=payload.nombre_completo, correo=payload.correo,
        telefono=payload.telefono, ciudad=payload.ciudad, username=payload.username,
        password_hash=hash_pw(payload.password), estado=payload.estado, cupo_credito=payload.cupo_credito
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"id_usuario": nuevo.id_usuario, "mensaje": "Usuario creado correctamente"}

@app.get("/api/categorias")
def obtener_categorias(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return [{"id_categoria": c.id_categoria, "nombre": c.nombre, "descripcion": c.descripcion, "estado": c.estado} for c in db.query(Categoria).all()]

class CategoriaReq(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""
    estado: str = "ACTIVA"

@app.post("/api/categorias", status_code=201)
def crear_categoria(req: CategoriaReq, db: Session = Depends(get_db), user=Depends(get_current_user)):
    c = Categoria(nombre=req.nombre, descripcion=req.descripcion, estado=req.estado)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id_categoria": c.id_categoria, "nombre": c.nombre}

@app.get("/api/productos")
def listar_productos(
    q: Optional[str] = None, id_categoria: Optional[int] = None,
    estado: Optional[str] = None, bajo_stock: Optional[bool] = False,
    db: Session = Depends(get_db), user=Depends(get_current_user)
):
    query = db.query(Producto)
    if q:
        busq = f"%{q}%"
        query = query.filter((Producto.nombre.ilike(busq)) | (Producto.sku.ilike(busq)) | (Producto.color.ilike(busq)))
    if id_categoria:
        query = query.filter(Producto.id_categoria == id_categoria)
    if estado:
        query = query.filter(Producto.estado == estado)
    if bajo_stock:
        query = query.filter(Producto.stock_actual <= Producto.stock_minimo)
    prods = query.order_by(Producto.id_producto.asc()).all()
    return [{
        "id_producto": p.id_producto, "id_categoria": p.id_categoria,
        "categoria": p.categoria.nombre if p.categoria else "",
        "sku": p.sku, "nombre": p.nombre, "talla": p.talla, "color": p.color,
        "precio_base": p.precio_base, "precio_sugerido": p.precio_sugerido,
        "stock_actual": p.stock_actual, "stock_minimo": p.stock_minimo, "estado": p.estado,
        "margen_unitario": p.precio_sugerido - p.precio_base,
        "alerta_stock": p.stock_actual <= p.stock_minimo
    } for p in prods]

class ProductoReq(BaseModel):
    id_categoria: int
    sku: str
    nombre: str
    talla: str
    color: str
    precio_base: float
    precio_sugerido: float
    stock_actual: int
    stock_minimo: int = 5
    estado: str = "ACTIVO"

@app.post("/api/productos", status_code=201)
def crear_prod(req: ProductoReq, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = Producto(**req.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id_producto": p.id_producto, "mensaje": "Producto creado"}

@app.put("/api/productos/{id_producto}")
def actualizar_prod(id_producto: int, req: ProductoReq, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    for k, v in req.model_dump().items():
        setattr(p, k, v)
    db.commit()
    return {"mensaje": "Producto actualizado"}

@app.delete("/api/productos/{id_producto}")
def eliminar_prod(id_producto: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p.estado = "INACTIVO"
    db.commit()
    return {"mensaje": "Producto desactivado correctamente"}

class ItemPedidoReq(BaseModel):
    id_producto: int
    cantidad: int

class PedidoReq(BaseModel):
    id_revendedor: Optional[int] = None
    tipo_pago: str
    observacion: Optional[str] = ""
    items: List[ItemPedidoReq]

@app.get("/api/pedidos")
def listar_pedidos(estado: Optional[str] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    query = db.query(Pedido)
    if user["rol"] == "REVENDEDOR":
        query = query.filter(Pedido.id_revendedor == user["id_usuario"])
    if estado:
        query = query.filter(Pedido.estado_pedido == estado)
    pedidos = query.order_by(Pedido.id_pedido.desc()).all()
    res = []
    for pe in pedidos:
        pagado = db.query(func.coalesce(func.sum(Pago.monto), 0.0)).filter(Pago.id_pedido == pe.id_pedido, Pago.estado_pago == "APLICADO").scalar()
        res.append({
            "id_pedido": pe.id_pedido, "codigo_pedido": pe.codigo_pedido,
            "id_revendedor": pe.id_revendedor, "revendedor": pe.revendedor.nombre_completo if pe.revendedor else "",
            "fecha_pedido": pe.fecha_pedido.strftime("%Y-%m-%d %H:%M"),
            "tipo_pago": pe.tipo_pago, "estado_pedido": pe.estado_pedido,
            "subtotal": pe.subtotal, "descuento_pct": pe.descuento_pct,
            "descuento_valor": pe.descuento_valor, "total": pe.total,
            "total_pagado": float(pagado), "saldo_pendiente": max(0.0, float(pe.total - pagado)),
            "observacion": pe.observacion
        })
    return res

@app.get("/api/pedidos/{id_pedido}")
def detalle_pedido(id_pedido: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pe = db.query(Pedido).filter(Pedido.id_pedido == id_pedido).first()
    if not pe:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    pagado = db.query(func.coalesce(func.sum(Pago.monto), 0.0)).filter(Pago.id_pedido == pe.id_pedido, Pago.estado_pago == "APLICADO").scalar()
    return {
        "id_pedido": pe.id_pedido, "codigo_pedido": pe.codigo_pedido,
        "revendedor": pe.revendedor.nombre_completo if pe.revendedor else "",
        "fecha_pedido": pe.fecha_pedido.strftime("%Y-%m-%d %H:%M"),
        "tipo_pago": pe.tipo_pago, "estado_pedido": pe.estado_pedido,
        "subtotal": pe.subtotal, "descuento_pct": pe.descuento_pct,
        "descuento_valor": pe.descuento_valor, "total": pe.total,
        "total_pagado": float(pagado), "saldo_pendiente": max(0.0, float(pe.total - pagado)),
        "observacion": pe.observacion,
        "items": [{
            "id_producto": d.id_producto, "sku": d.producto.sku if d.producto else "",
            "nombre": d.producto.nombre if d.producto else "", "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario, "subtotal_linea": d.subtotal_linea
        } for d in pe.detalles]
    }

@app.post("/api/pedidos", status_code=201)
def crear_pedido(req: PedidoReq, db: Session = Depends(get_db), user=Depends(get_current_user)):
    id_rev = req.id_revendedor if user["rol"] in ("ADMIN", "VENDEDOR") and req.id_revendedor else user["id_usuario"]
    total_unidades = sum(i.cantidad for i in req.items)
    desc_pct = 12.0 if total_unidades >= 25 else (8.0 if total_unidades >= 12 else (5.0 if total_unidades >= 6 else 0.0))

    subtotal = 0.0
    lineas = []
    for item in req.items:
        prod = db.query(Producto).filter(Producto.id_producto == item.id_producto).first()
        if not prod or prod.stock_actual < item.cantidad:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {prod.nombre if prod else 'producto'}")
        prod.stock_actual -= item.cantidad
        sub_l = prod.precio_base * item.cantidad
        subtotal += sub_l
        lineas.append((prod.id_producto, item.cantidad, prod.precio_base, sub_l))

    desc_val = round(subtotal * (desc_pct / 100.0), 2)
    total = round(subtotal - desc_val, 2)
    codigo = f"PED-{datetime.now().strftime('%m%d%H%M%S')}"

    nuevo_p = Pedido(
        codigo_pedido=codigo, id_revendedor=id_rev, tipo_pago=req.tipo_pago,
        estado_pedido="PENDIENTE", subtotal=subtotal, descuento_pct=desc_pct,
        descuento_valor=desc_val, total=total, observacion=req.observacion
    )
    db.add(nuevo_p)
    db.flush()

    for id_pr, cant, p_unit, sub_l in lineas:
        db.add(DetallePedido(id_pedido=nuevo_p.id_pedido, id_producto=id_pr, cantidad=cant, precio_unitario=p_unit, subtotal_linea=sub_l))

    db.commit()
    db.refresh(nuevo_p)
    return {"id_pedido": nuevo_p.id_pedido, "codigo_pedido": codigo, "total": total}

@app.get("/api/pagos")
def listar_pagos(db: Session = Depends(get_db), user=Depends(get_current_user)):
    pagos = db.query(Pago).order_by(Pago.id_pago.desc()).all()
    return [{
        "id_pago": p.id_pago, "id_pedido": p.id_pedido,
        "fecha_pago": p.fecha_pago.strftime("%Y-%m-%d %H:%M"),
        "monto": p.monto, "metodo_pago": p.metodo_pago,
        "referencia": p.referencia, "estado_pago": p.estado_pago, "observacion": p.observacion
    } for p in pagos]

class PagoReq(BaseModel):
    id_pedido: int
    monto: float
    metodo_pago: str
    referencia: Optional[str] = ""
    observacion: Optional[str] = ""

@app.post("/api/pagos", status_code=201)
def registrar_pago(req: PagoReq, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pe = db.query(Pedido).filter(Pedido.id_pedido == req.id_pedido).first()
    if not pe:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    nuevo = Pago(id_pedido=req.id_pedido, monto=req.monto, metodo_pago=req.metodo_pago, referencia=req.referencia, observacion=req.observacion)
    db.add(nuevo)
    db.flush()
    pagado = db.query(func.coalesce(func.sum(Pago.monto), 0.0)).filter(Pago.id_pedido == pe.id_pedido, Pago.estado_pago == "APLICADO").scalar()
    if pagado >= pe.total:
        pe.estado_pedido = "PAGADO"
    db.commit()
    return {"id_pago": nuevo.id_pago, "mensaje": "Pago aplicado correctamente"}

@app.get("/api/reportes/dashboard")
def obtener_dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    total_prods = db.query(Producto).filter(Producto.estado == "ACTIVO").count()
    bajo_stock = db.query(Producto).filter(Producto.estado == "ACTIVO", Producto.stock_actual <= Producto.stock_minimo).count()
    total_pedidos = db.query(Pedido).count()
    ventas = db.query(func.coalesce(func.sum(Pedido.total), 0.0)).filter(Pedido.estado_pedido != "CANCELADO").scalar()
    recaudado = db.query(func.coalesce(func.sum(Pago.monto), 0.0)).filter(Pago.estado_pago == "APLICADO").scalar()
    return {
        "kpis": {
            "productos_activos": total_prods,
            "productos_bajo_stock": bajo_stock,
            "total_pedidos": total_pedidos,
            "ventas_totales": float(ventas),
            "total_recaudado": float(recaudado),
            "cartera_pendiente": max(0.0, float(ventas - recaudado))
        },
        "ventas_por_categoria": [],
        "top_productos": [],
        "cartera_revendedores": []
    }

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.get("/")
def root():
    return RedirectResponse(url="/app/login.html")

