from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.applications.routes import router as applications_router
from app.api.citizens.routes import router as citizens_router
from app.api.payments.routes import router as payments_router
from app.api.popup_city.routes import router as popup_cities_router
from app.api.products.routes import router as products_router
from app.api.webhooks.routes import router as webhooks_router
from app.core.config import Environment, settings
from app.core.database import create_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT != Environment.TEST:
        create_db()
    yield


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(applications_router, prefix='/applications', tags=['Applications'])
app.include_router(citizens_router, prefix='/citizens', tags=['Citizens'])
app.include_router(payments_router, prefix='/payments', tags=['Payments'])
app.include_router(popup_cities_router, prefix='/popups', tags=['Popups'])
app.include_router(products_router, prefix='/products', tags=['Products'])
app.include_router(webhooks_router, prefix='/webhooks', tags=['Webhooks'])

origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/', include_in_schema=False)
def ping():
    return Response(status_code=200)
