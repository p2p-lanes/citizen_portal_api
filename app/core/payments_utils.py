from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.payments import schemas
from app.api.products.crud import product as product_crud
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.security import TokenData


def create_payment(db: Session, obj: schemas.PaymentCreate, user: TokenData):
    application = application_crud.get(db, obj.application_id, user)

    products = product_crud.find(
        db=db,
        filters=ProductFilter(
            id_in=obj.products,
            popup_city_id=application.popup_city_id,
            is_active=True,
        ),
        user=user,
    )
    if len(products) != len(obj.products):
        raise HTTPException(status_code=400, detail='Some products are not available')
    amount = sum(product.price for product in products)
    reference = {
        'email': application.email,
        'application_id': application.id,
        'products': [
            {'product_id': product.id, 'name': product.name} for product in products
        ],
    }

    payment_request = simplefi.create_payment(amount, reference=reference)

    return {
        'products': obj.products,
        'products_data': [product.name for product in products],
        'application_id': application.id,
        'citizen_id': application.citizen_id,
        'external_id': payment_request['id'],
        'status': payment_request['status'],
        'amount': amount,
        'currency': 'USD',
        'checkout_url': payment_request['checkout_url'],
    }
