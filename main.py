from fastapi import FastAPI, Response

from app.api.applications.routes import router as applications_router
from app.api.citizens.routes import router as citizens_router
from app.api.products.routes import router as products_router
from app.core.database import create_db

app = FastAPI()

create_db()
# Include routers
app.include_router(applications_router, prefix='/applications', tags=['applications'])
app.include_router(citizens_router, prefix='/citizens', tags=['citizens'])
app.include_router(products_router, prefix='/products', tags=['products'])


@app.get('/', include_in_schema=False)
def ping():
    return Response(status_code=200)
