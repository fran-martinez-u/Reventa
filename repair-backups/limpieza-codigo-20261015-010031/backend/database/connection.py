"""Conexión compartida. La URL se guarda en .env, fuera del código."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
env_file = ROOT / '.env'
if env_file.exists():
    for line in env_file.read_text(encoding='utf-8-sig').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    raise RuntimeError('Configura DATABASE_URL en el archivo .env del proyecto.')
DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
