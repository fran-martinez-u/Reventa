import psycopg2
import hashlib

DATABASE_URL = "postgresql://neondb_owner:npg_YRVq15IiSTDn@ep-icy-butterfly-b5elmp3c-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def inicializar():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;

    CREATE TABLE roles (
        id_rol SERIAL PRIMARY KEY,
        nombre VARCHAR(30) NOT NULL UNIQUE,
        descripcion VARCHAR(150) NOT NULL,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    CREATE TABLE usuarios (
        id_usuario SERIAL PRIMARY KEY,
        id_rol INTEGER NOT NULL REFERENCES roles(id_rol),
        nombre VARCHAR(100) NOT NULL,
        correo VARCHAR(120) NOT NULL UNIQUE,
        telefono VARCHAR(20),
        password_hash VARCHAR(255) NOT NULL,
        activo SMALLINT DEFAULT 1 NOT NULL,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    CREATE TABLE categorias (
        id_categoria SERIAL PRIMARY KEY,
        nombre VARCHAR(80) NOT NULL UNIQUE,
        descripcion VARCHAR(200),
        estado VARCHAR(15) DEFAULT 'ACTIVO' NOT NULL,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    CREATE TABLE productos (
        id_producto SERIAL PRIMARY KEY,
        id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria),
        codigo VARCHAR(30) NOT NULL UNIQUE,
        nombre VARCHAR(120) NOT NULL,
        descripcion VARCHAR(250),
        precio_base NUMERIC(12,2) NOT NULL,
        precio_reventa_sugerido NUMERIC(12,2) NOT NULL,
        stock_actual INTEGER DEFAULT 0 NOT NULL,
        stock_minimo INTEGER DEFAULT 5 NOT NULL,
        estado VARCHAR(15) DEFAULT 'ACTIVO' NOT NULL,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    CREATE TABLE pedidos (
        id_pedido SERIAL PRIMARY KEY,
        id_revendedor INTEGER NOT NULL REFERENCES usuarios(id_usuario),
        id_vendedor INTEGER REFERENCES usuarios(id_usuario),
        fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        estado VARCHAR(20) DEFAULT 'PENDIENTE' NOT NULL,
        subtotal NUMERIC(12,2) DEFAULT 0 NOT NULL,
        descuento_porcentaje NUMERIC(5,2) DEFAULT 0 NOT NULL,
        descuento_monto NUMERIC(12,2) DEFAULT 0 NOT NULL,
        total NUMERIC(12,2) DEFAULT 0 NOT NULL,
        observaciones VARCHAR(250)
    );

    CREATE TABLE detalle_pedido (
        id_detalle SERIAL PRIMARY KEY,
        id_pedido INTEGER NOT NULL REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
        id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
        cantidad INTEGER NOT NULL,
        precio_unitario NUMERIC(12,2) NOT NULL,
        subtotal NUMERIC(12,2) NOT NULL
    );

    CREATE TABLE pagos (
        id_pago SERIAL PRIMARY KEY,
        id_pedido INTEGER NOT NULL REFERENCES pedidos(id_pedido),
        fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        monto NUMERIC(12,2) NOT NULL,
        metodo_pago VARCHAR(30) NOT NULL,
        referencia_transaccion VARCHAR(60),
        estado_pago VARCHAR(20) DEFAULT 'CONFIRMADO' NOT NULL,
        registrado_por INTEGER NOT NULL REFERENCES usuarios(id_usuario)
    );
    """)

    cur.execute("""
    INSERT INTO roles (id_rol, nombre, descripcion) VALUES
    (1, 'ADMIN', 'Administrador general del sistema'),
    (2, 'VENDEDOR', 'Gestiona catálogo, pedidos y pagos'),
    (3, 'REVENDEDOR', 'Realiza pedidos y consulta sus pagos');
    """)

    pw_admin = hash_password('Admin123*')
    pw_vend = hash_password('Vendedor123*')
    pw_rev = hash_password('Revendedor123*')

    cur.execute("""
    INSERT INTO usuarios (id_rol, nombre, correo, telefono, password_hash, activo) VALUES
    (1, 'Neitan Narvaez', 'neitannarvaez@outlook.com', '3001112233', %s, 1),
    (1, 'Administrador General', 'admin@reventa.com', '3001112233', %s, 1),
    (2, 'Laura Vendedora', 'vendedor@reventa.com', '3002223344', %s, 1),
    (3, 'Carlos Revendedor', 'carlos@reventa.com', '3003334455', %s, 1);
    """, (pw_admin, pw_admin, pw_vend, pw_rev))

    cur.execute("""
    INSERT INTO categorias (nombre, descripcion, estado) VALUES
    ('Camisetas', 'Camisetas urbanas y básicas', 'ACTIVO'),
    ('Jeans', 'Jeans masculinos y femeninos', 'ACTIVO'),
    ('Chaquetas', 'Chaquetas livianas y denim', 'ACTIVO'),
    ('Calzado', 'Tenis y calzado casual', 'ACTIVO');

    INSERT INTO productos (id_categoria, codigo, nombre, descripcion, precio_base, precio_reventa_sugerido, stock_actual, stock_minimo, estado) VALUES
    (1, 'CAM-001', 'Camiseta Básica Premium', 'Algodón 100% talla M', 28000, 45000, 45, 8, 'ACTIVO'),
    (1, 'CAM-002', 'Camiseta Oversize Street', 'Estampado abstracto', 34000, 55000, 32, 6, 'ACTIVO'),
    (2, 'JEA-001', 'Jean Slim Fit Clásico', 'Azul oscuro talla 32', 68000, 105000, 22, 5, 'ACTIVO'),
    (3, 'CHA-001', 'Chaqueta Denim Unisex', 'Azul medio talla M', 95000, 145000, 10, 3, 'ACTIVO'),
    (4, 'CAL-001', 'Tenis Urbanos Blancos', 'Suela antideslizante', 89000, 139000, 4, 5, 'ACTIVO');
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente en Neon.")

if __name__ == "__main__":
    inicializar()
