from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.applications.schemas import ApplicationStatus
from app.api.discount_codes.crud import discount_code as discount_code_crud
from app.api.payments import schemas
from app.api.payments.models import PaymentProduct
from app.api.payments.schemas import InternalPaymentCreate
from app.api.products.crud import product as product_crud
from app.api.products.models import Product
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.security import TokenData


def _get_price(product: Product, discount_value: float, discount_type: str) -> float:
    if discount_type == 'percentage':
        return round(product.price * (1 - discount_value / 100), 2)
    elif discount_type == 'fixed':
        return round(product.price - discount_value, 2)
    return product.price


def _calculate_price(
    products: List[Product],
    products_data: dict[int, PaymentProduct],
    discount_value: float,
    discount_type: str,
) -> float:
    if patreon := next((p for p in products if p.category == 'patreon'), None):
        return _get_price(patreon, discount_assigned=0)

    amounts = {}
    for p in products:
        pdata = products_data[p.id]
        attendee_id = pdata.attendee_id
        _amount = _get_price(p, discount_value, discount_type) * pdata.quantity
        amounts[attendee_id] = (
            _amount + amounts.get(attendee_id, 0)
            if p.category != 'supporter'
            else _get_price(p, discount_value=0, discount_type=discount_type)
        )

    return sum(amounts.values())


def create_payment(
    db: Session,
    obj: schemas.PaymentCreate,
    user: TokenData,
) -> InternalPaymentCreate:
    application = application_crud.get(db, obj.application_id, user)
    if application.status != ApplicationStatus.ACCEPTED.value:
        raise HTTPException(status_code=400, detail='Application is not accepted')

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

    application_products = [p for a in application.attendees for p in a.products]
    already_patreon = any(p.slug == 'patreon' for p in application_products)

    price_zero_payment = InternalPaymentCreate(
        products=obj.products,
        application_id=application.id,
        external_id=None,
        status='approved',
        amount=0,
        currency='USD',
        checkout_url=None,
    )
    if already_patreon:
        return price_zero_payment

    discount_assigned = application.discount_assigned or 0

    amount = _calculate_price(
        products,
        products_data,
        discount_value=discount_assigned,
        discount_type='percentage',
    )
    if obj.discount_code:
        discount_code = discount_code_crud.get_by_code(
            db,
            code=obj.discount_code,
            popup_city_id=application.popup_city_id,
        )
        amount2 = _calculate_price(
            products,
            products_data,
            discount_value=discount_code.discount_value,
            discount_type=discount_code.discount_type,
        )
        amount = min(amount, amount2)

    if amount == 0:
        return price_zero_payment

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

    if not (api_key := application.popup_city.simplefi_api_key):
        raise HTTPException(
            status_code=400, detail='Popup city does not have a Simplefi API key'
        )

    payment_request = simplefi.create_payment(
        amount,
        reference=reference,
        simplefi_api_key=api_key,
    )

    return InternalPaymentCreate(
        products=obj.products,
        application_id=application.id,
        external_id=payment_request['id'],
        status=payment_request['status'],
        amount=amount,
        currency='USD',
        checkout_url=payment_request['checkout_url'],
    )
