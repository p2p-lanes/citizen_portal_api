from app.api.base_crud import CRUDBase
from app.api.products import models, schemas


class CRUDProduct(
    CRUDBase[models.Product, schemas.ProductCreate, schemas.ProductUpdate]
):
    pass


product = CRUDProduct(models.Product)
