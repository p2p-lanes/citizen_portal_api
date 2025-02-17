from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.applications.schemas import ApplicationStatus
from app.api.coupon_codes.crud import coupon_code as coupon_code_crud
from app.api.payments import schemas
from app.api.payments.models import PaymentProduct
from app.api.payments.schemas import InternalPaymentCreate
from app.api.products.crud import product as product_crud
from app.api.products.models import Product
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.security import TokenData


def _get_discounted_price(price: float, discount_value: float) -> float:
    return round(price * (1 - discount_value / 100), 2)


def _calculate_price(
    products: List[Product],
    products_data: dict[int, PaymentProduct],
    discount_value: float,
    credit: float,
) -> float:
    if patreon := next((p for p in products if p.category == 'patreon'), None):
        return _get_discounted_price(patreon.price, discount_value=0)

    standard_amount = 0
    supporter_amount = 0
    for p in products:
        quantity = products_data[p.id].quantity
        if p.category == 'supporter':
            supporter_amount += p.price * quantity
        else:
            standard_amount += p.price * quantity

    standard_amount = standard_amount - credit
    if standard_amount > 0:
        standard_amount = _get_discounted_price(standard_amount, discount_value)

    return standard_amount + supporter_amount


def create_payment(
    db: Session,
    obj: schemas.PaymentCreate,
    user: TokenData,
) -> InternalPaymentCreate:
    application = application_crud.get(db, obj.application_id, user)
    if application.status != ApplicationStatus.ACCEPTED.value:
        raise HTTPException(status_code=400, detail='Application is not accepted')

    credit = application.get_credit() if obj.edit_passes else 0

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

    response = InternalPaymentCreate(
        products=obj.products,
        application_id=application.id,
        currency='USD',
    )

    if already_patreon:
        response.status = 'approved'
        response.amount = 0
        return response

    discount_assigned = application.discount_assigned or 0

    response.amount = _calculate_price(
        products,
        products_data,
        discount_value=discount_assigned,
        credit=credit,
    )

    if obj.coupon_code:
        coupon_code = coupon_code_crud.get_by_code(
            db,
            code=obj.coupon_code,
            popup_city_id=application.popup_city_id,
        )
        discounted_amount = _calculate_price(
            products,
            products_data,
            discount_value=coupon_code.discount_value,
            credit=credit,
        )
        if discounted_amount < response.amount:
            response.amount = discounted_amount
            response.coupon_code_id = coupon_code.id
            response.coupon_code = coupon_code.code
            response.discount_value = coupon_code.discount_value

    if response.amount <= 0:
        response.status = 'approved'
        if response.amount < 0:
            application.credit = -response.amount
            response.amount = 0
        else:
            application.credit = 0
        db.commit()
        db.refresh(application)

        return response

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
        response.amount,
        reference=reference,
        simplefi_api_key=api_key,
    )

    response.external_id = payment_request['id']
    response.status = payment_request['status']
    response.checkout_url = payment_request['checkout_url']

    return response
