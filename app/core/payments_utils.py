from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.payments import schemas
from app.api.payments.schemas import InternalPaymentCreate
from app.api.products.crud import product as product_crud
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.security import TokenData


def create_payment(
    db: Session,
    obj: schemas.PaymentCreate,
    user: TokenData,
) -> InternalPaymentCreate:
    application = application_crud.get(db, obj.application_id, user)

    product_ids = [p.product_id for p in obj.products]
    products_data = {p.product_id: p for p in obj.products}
    products = product_crud.find(
        db=db,
        filters=ProductFilter(
            id_in=product_ids,
            popup_city_id=application.popup_city_id,
            is_active=True,
        ),
        user=user,
    )
    if len(products) != len(product_ids):
        raise HTTPException(status_code=400, detail='Some products are not available')

    if application.ticket_category == 'scholarship':
        return InternalPaymentCreate(
            products=obj.products,
            application_id=application.id,
            external_id=None,
            status='approved',
            amount=0,
            currency='USD',
            checkout_url=None,
        )

    patreon_product = next((p for p in products if p.slug == 'patreon'), None)
    if patreon_product:
        amount = patreon_product.price
    else:
        amount = sum(p.price * products_data[p.id].quantity for p in products)

    reference = {
        'email': application.email,
        'application_id': application.id,
        'products': [
            {
                'product_id': product.id,
                'name': product.name,
                'quantity': products_data[product.id].quantity,
                'attendee_id': products_data[product.id].attendee_id,
            }
            for product in products
        ],
    }

    payment_request = simplefi.create_payment(amount, reference=reference)

    return InternalPaymentCreate(
        products=obj.products,
        application_id=application.id,
        external_id=payment_request['id'],
        status=payment_request['status'],
        amount=amount,
        currency='USD',
        checkout_url=payment_request['checkout_url'],
    )
