"""Punto de entrada: publica la API y los archivos HTML del proyecto."""
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend.routers import auth, catalogo, ventas, reportes

app = FastAPI(title='Reventa', description='Gestión de productos, pedidos y pagos.', version='2.0')
app.include_router(auth.router)
app.include_router(catalogo.router)
app.include_router(ventas.router)
app.include_router(reportes.router)


@app.exception_handler(RequestValidationError)
async def datos_invalidos(request, exc):
    campos = ', '.join(dict.fromkeys(str(error['loc'][-1]) for error in exc.errors()))
    return JSONResponse(status_code=422, content={'detail': f'Revisa los datos de: {campos}. Completa los campos y verifica sus límites.'})


@app.exception_handler(IntegrityError)
async def conflicto(request, exc):
    return JSONResponse(status_code=409, content={'detail': 'El registro está repetido o tiene una relación no válida. Revisa los datos.'})


@app.exception_handler(SQLAlchemyError)
async def error_base(request, exc):
    logging.getLogger(__name__).error('No se pudo completar una operación de base de datos: %s', type(exc).__name__)
    return JSONResponse(status_code=503, content={'detail': 'No fue posible acceder a la base de datos. Intenta de nuevo.'})


@app.middleware('http')
async def archivos_actualizados(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/app/'):
        response.headers['Cache-Control'] = 'no-store'
    return response


@app.get('/', include_in_schema=False)
def inicio():
    return RedirectResponse('/app/login.html')


app.mount('/app', StaticFiles(directory=Path(__file__).resolve().parents[1] / 'frontend', html=True), name='frontend')
