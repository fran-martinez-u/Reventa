"""Crear el primer administrador en una base nueva, desde la terminal."""

from getpass import getpass
from sqlalchemy import func
from backend.database.connection import SessionLocal
from backend.models.models import Usuario, Rol
from backend.schemas.schemas import UsuarioCrear
from backend.services.auth import hash_password


def main():
    with SessionLocal() as db:
        role = db.query(Rol).filter(Rol.nombre == "ADMIN").first()
        if not role:
            raise SystemExit("Primero ejecuta los scripts SQL de tablas y roles.")
        nombre = input("Nombre: ").strip()
        correo = input("Correo: ").strip().lower()
        password = getpass("Contraseña (mínimo 8 caracteres): ")
        if password != getpass("Repite la contraseña: "):
            raise SystemExit("Las contraseñas no coinciden.")
        data = UsuarioCrear(
            nombre=nombre, correo=correo, id_rol=role.id_rol, contrasena=password
        )
        if db.query(Usuario).filter(func.lower(Usuario.correo) == data.correo).first():
            raise SystemExit("Ese correo ya está registrado.")
        db.add(
            Usuario(
                **data.model_dump(exclude={"contrasena"}),
                password_hash=hash_password(password)
            )
        )
        db.commit()
        print("Administrador creado.")


if __name__ == "__main__":
    main()
