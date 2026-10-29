"""Pruebas con el cliente de FastAPI y una base temporal; no modifican Neon."""

import os
import unittest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite://")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.main import app
from backend.database.connection import Base, get_db
from backend.models.models import Rol, Usuario, Categoria, Producto
from backend.services.auth import SESIONES, hash_password

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestSession = sessionmaker(bind=engine, autoflush=False)
PASSWORD = "Solo-Pruebas-123"
HASH = hash_password(PASSWORD)


def test_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def request(method, path, data=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    with TestClient(app) as client:
        response = client.request(method, path, json=data, headers=headers)
    return response.status_code, response.json()


def seed():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SESIONES.clear()
    with TestSession() as db:
        for id, name in [(1, "ADMIN"), (2, "VENDEDOR"), (3, "REVENDEDOR")]:
            db.add(Rol(id_rol=id, nombre=name, descripcion=name))
        for id, role in [(1, 1), (2, 2), (3, 3), (4, 3)]:
            db.add(
                Usuario(
                    id_usuario=id,
                    id_rol=role,
                    nombre=f"Usuario {id}",
                    correo=f"user{id}@example.invalid",
                    password_hash=HASH,
                    activo=1,
                )
            )
        db.add(Categoria(id_categoria=1, nombre="Camisetas", estado="ACTIVO"))
        db.add(
            Producto(
                id_producto=1,
                id_categoria=1,
                codigo="CAM-001",
                nombre="Camiseta",
                descripcion="",
                precio_base=100,
                precio_reventa_sugerido=150,
                stock_actual=20,
                stock_minimo=5,
                estado="ACTIVO",
            )
        )
        db.commit()


class ApplicationTests(unittest.TestCase):
    def test_documentation_and_five_complete_crud_modules(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/docs").status_code, 200)
            schema = client.get("/openapi.json").json()
        for resource in [
            "categorias",
            "productos",
            "pedidos",
            "pagos",
            "auth/usuarios",
        ]:
            path = "/api/" + resource
            detail = path + (
                "/{id_usuario}" if resource == "auth/usuarios" else "/{id}"
            )
            self.assertTrue({"get", "post"}.issubset(schema["paths"][path]))
            self.assertTrue({"get", "put", "delete"}.issubset(schema["paths"][detail]))

    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def setUp(self):
        app.dependency_overrides[get_db] = test_db
        seed()
        self.admin = self.login(1)
        self.seller = self.login(2)
        self.customer = self.login(3)
        self.other = self.login(4)

    def tearDown(self):
        app.dependency_overrides.clear()

    def login(self, id):
        status, result = request(
            "POST",
            "/api/auth/login",
            {"correo": f"user{id}@example.invalid", "contrasena": PASSWORD},
        )
        self.assertEqual(status, 200)
        return result["access_token"]

    def call(self, method, path, data=None, token=None, status=200):
        code, body = request(method, path, data, token or self.admin)
        self.assertEqual(code, status, body)
        return body

    def order(self, quantity=2, token=None):
        return self.call(
            "POST",
            "/api/pedidos",
            {"id_revendedor": 3, "items": [{"id_producto": 1, "cantidad": quantity}]},
            token,
            status=201,
        )

    def stock(self):
        return self.call("GET", "/api/productos/1")["stock_actual"]

    def payment(self, order, amount=100):
        return self.call(
            "POST",
            "/api/pagos",
            {
                "id_pedido": order["id_pedido"],
                "monto": amount,
                "metodo_pago": "EFECTIVO",
            },
            self.seller,
            status=201,
        )

    def test_login_logout_and_private_data(self):
        me = self.call("GET", "/api/auth/me")
        self.assertEqual(me["rol"], "ADMIN")
        self.assertNotIn("password_hash", me)
        self.call("POST", "/api/auth/logout")
        self.call("GET", "/api/auth/me", status=401)
        self.assertEqual(request("GET", "/api/productos")[0], 401)
        self.assertEqual(
            request(
                "POST",
                "/api/auth/login",
                {"correo": "user1@example.invalid", "contrasena": "incorrecta"},
            )[0],
            401,
        )

    def test_password_legacy_upgrade(self):
        import hashlib

        with TestSession() as db:
            db.get(Usuario, 3).password_hash = hashlib.sha256(
                PASSWORD.encode()
            ).hexdigest()
            db.commit()
        self.login(3)
        with TestSession() as db:
            self.assertTrue(
                db.get(Usuario, 3).password_hash.startswith("pbkdf2_sha256$")
            )

    def test_catalog_crud_and_search(self):
        c = self.call("POST", "/api/categorias", {"nombre": "Calzado"}, status=201)
        cid = c["id_categoria"]
        self.call(
            "PUT",
            f"/api/categorias/{cid}",
            {"nombre": "Zapatos", "descripcion": "Casuales"},
        )
        self.assertEqual(len(self.call("GET", "/api/categorias?q=zap")), 1)
        self.call("DELETE", f"/api/categorias/{cid}")
        self.assertEqual(
            self.call("GET", f"/api/categorias/{cid}")["estado"], "INACTIVO"
        )
        data = self.call("GET", "/api/productos/1")
        data = {
            key: data[key]
            for key in [
                "id_categoria",
                "codigo",
                "nombre",
                "descripcion",
                "precio_base",
                "precio_reventa_sugerido",
                "stock_actual",
                "stock_minimo",
                "estado",
            ]
        }
        data["codigo"] = "CAM-002"
        p = self.call("POST", "/api/productos", data, status=201)
        pid = p["id_producto"]
        data["nombre"] = "Nueva prenda"
        self.call("PUT", f"/api/productos/{pid}", data)
        self.assertEqual(
            len(self.call("GET", "/api/productos?q=nueva&estado=ACTIVO")), 1
        )
        self.call("DELETE", f"/api/productos/{pid}")
        self.assertEqual(
            self.call("GET", f"/api/productos/{pid}")["estado"], "INACTIVO"
        )

    def test_roles_enforced_by_server(self):
        self.call(
            "POST", "/api/categorias", {"nombre": "Bloqueado"}, self.seller, status=403
        )
        self.call("DELETE", "/api/productos/1", token=self.customer, status=403)
        self.call("GET", "/api/auth/usuarios", token=self.seller, status=403)
        self.call("POST", "/api/auth/usuarios", {}, self.seller, status=403)
        self.call("GET", "/api/auth/revendedores", token=self.seller)
        self.call(
            "POST",
            "/api/pagos",
            {"id_pedido": 1, "monto": 1, "metodo_pago": "EFECTIVO"},
            self.customer,
            status=403,
        )

    def test_user_crud_and_deactivated_session(self):
        data = {
            "nombre": "Nueva cuenta",
            "correo": "nueva@example.invalid",
            "id_rol": 3,
            "contrasena": PASSWORD,
        }
        new = self.call("POST", "/api/auth/usuarios", data, status=201)
        id = new["id_usuario"]
        data.pop("contrasena")
        data["nombre"] = "Cuenta editada"
        self.call("PUT", f"/api/auth/usuarios/{id}", data)
        self.assertEqual(len(self.call("GET", "/api/auth/usuarios?q=editada")), 1)
        self.call("DELETE", f"/api/auth/usuarios/{id}")
        self.assertEqual(self.call("GET", f"/api/auth/usuarios/{id}")["activo"], 0)
        self.call("DELETE", "/api/auth/usuarios/3")
        self.call("GET", "/api/auth/me", token=self.customer, status=401)
        self.call("DELETE", "/api/auth/usuarios/1", status=400)

    def test_order_crud_stock_and_cancel_idempotent(self):
        order = self.order(2, self.customer)
        id = order["id_pedido"]
        self.assertEqual(self.stock(), 18)
        self.assertEqual(float(order["total"]), 200)
        data = {
            "items": [{"id_producto": 1, "cantidad": 3}],
            "observaciones": "Editado",
        }
        self.call("PUT", f"/api/pedidos/{id}", data, self.customer)
        self.assertEqual(self.stock(), 17)
        self.call("DELETE", f"/api/pedidos/{id}", token=self.customer)
        self.assertEqual(self.stock(), 20)
        self.call("DELETE", f"/api/pedidos/{id}", token=self.customer)
        self.assertEqual(self.stock(), 20)

    def test_owner_cannot_access_other_orders_payments_or_reports(self):
        order = self.order(token=self.customer)
        payment = self.payment(order)
        self.call(
            "GET", f'/api/pedidos/{order["id_pedido"]}', token=self.other, status=404
        )
        self.call(
            "DELETE", f'/api/pedidos/{order["id_pedido"]}', token=self.other, status=404
        )
        self.call(
            "GET", f'/api/pagos/{payment["id_pago"]}', token=self.other, status=404
        )
        self.assertEqual(self.call("GET", "/api/pedidos", token=self.other), [])
        self.assertEqual(self.call("GET", "/api/pagos", token=self.other), [])
        self.assertEqual(
            self.call("GET", "/api/reportes/ventas-revendedor", token=self.other), []
        )
        self.assertEqual(
            float(
                self.call("GET", "/api/reportes/dashboard", token=self.other)["ventas"]
            ),
            0,
        )

    def test_invalid_stock_rollback_and_duplicate_lines(self):
        self.order(2)
        self.call(
            "POST",
            "/api/pedidos",
            {"id_revendedor": 3, "items": [{"id_producto": 1, "cantidad": 999}]},
            status=400,
        )
        self.assertEqual(self.stock(), 18)
        self.call(
            "PUT",
            "/api/pedidos/1",
            {"id_revendedor": 3, "items": [{"id_producto": 1, "cantidad": 999}]},
            status=400,
        )
        self.assertEqual(self.stock(), 18)
        self.assertEqual(self.call("GET", "/api/pedidos/1")["items"][0]["cantidad"], 2)
        self.call(
            "POST",
            "/api/pedidos",
            {"items": [{"id_producto": 1, "cantidad": 1}] * 2},
            self.customer,
            status=422,
        )

    def test_payment_crud_balance_and_protected_order(self):
        order = self.order()
        payment = self.payment(order, 50)
        id = payment["id_pago"]
        self.call(
            "POST",
            "/api/pagos",
            {"id_pedido": order["id_pedido"], "monto": 151, "metodo_pago": "EFECTIVO"},
            status=400,
        )
        self.call("DELETE", "/api/pedidos/1", status=400)
        data = {
            "id_pedido": order["id_pedido"],
            "monto": 200,
            "metodo_pago": "TRANSFERENCIA",
            "referencia_transaccion": "TEST",
        }
        self.call("PUT", f"/api/pagos/{id}", data)
        updated = self.call("GET", "/api/pedidos/1")
        self.assertEqual(float(updated["saldo"]), 0)
        self.assertEqual(updated["estado"], "CONFIRMADO")
        self.call("DELETE", f"/api/pagos/{id}", token=self.seller, status=403)
        self.call("DELETE", f"/api/pagos/{id}")
        self.assertEqual(self.call("GET", f"/api/pagos/{id}")["estado_pago"], "ANULADO")
        self.assertEqual(float(self.call("GET", "/api/pedidos/1")["saldo"]), 200)
        self.call("DELETE", "/api/pedidos/1")
        self.assertEqual(self.stock(), 20)

    def test_validation_duplicates_and_not_found(self):
        self.call("POST", "/api/categorias", {"nombre": "Camisetas"}, status=409)
        self.call(
            "GET", "/api/categorias/1"
        )  # La transacción fallida no daña la siguiente petición.
        self.call("GET", "/api/productos/999", status=404)
        self.call(
            "POST",
            "/api/auth/usuarios",
            {"nombre": "XX", "correo": "invalido", "id_rol": 3, "contrasena": PASSWORD},
            status=422,
        )
        self.call(
            "POST",
            "/api/auth/usuarios",
            {
                "nombre": "  ",
                "correo": "valido@example.invalid",
                "id_rol": 3,
                "contrasena": PASSWORD,
            },
            status=422,
        )
        self.call(
            "POST",
            "/api/pedidos",
            {"items": [{"id_producto": 1, "cantidad": 0}]},
            self.customer,
            status=422,
        )
        self.call(
            "POST",
            "/api/pagos",
            {"id_pedido": 1, "monto": -10, "metodo_pago": "EFECTIVO"},
            status=422,
        )
        self.call(
            "POST",
            "/api/productos",
            {
                "id_categoria": 1,
                "codigo": "XX",
                "nombre": "Test",
                "precio_base": -10,
                "precio_reventa_sugerido": 10,
                "stock_actual": 0,
            },
            status=422,
        )

    def test_dashboard_reports_and_filters(self):
        order = self.order()
        self.payment(order, 50)
        stats = self.call("GET", "/api/reportes/dashboard")
        self.assertEqual(float(stats["ventas"]), 200)
        self.assertEqual(float(stats["recaudado"]), 50)
        self.assertEqual(float(stats["saldo"]), 150)
        report = self.call("GET", "/api/reportes/ventas-revendedor")
        self.assertEqual(float(report[0]["ventas"]), 200)
        self.assertEqual(self.call("GET", "/api/reportes/inventario")[0]["stock"], 18)
        self.assertEqual(len(self.call("GET", "/api/pedidos?estado=PENDIENTE")), 1)
        self.assertEqual(self.call("GET", "/api/pedidos?estado=CANCELADO"), [])
        self.assertEqual(len(self.call("GET", "/api/pagos?id_pedido=1")), 1)


if __name__ == "__main__":
    unittest.main()
