from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.applications.models import Application
from app.api.applications.schemas import ApplicationStatus
from app.api.coupon_codes.crud import coupon_code as coupon_code_crud
from app.api.payments import schemas
from app.api.payments.models import PaymentProduct
from app.api.payments.schemas import InternalPaymentCreate
from app.api.products.crud import product as product_crud
from app.api.products.models import Product
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.logger import logger
from app.core.security import TokenData


def _get_discounted_price(price: float, discount_value: float) -> float:
    return round(price * (1 - discount_value / 100), 2)


def _get_credit(application: Application, discount_value: float) -> float:
    total = 0
    for a in application.attendees:
        patreon = False
        subtotal = 0
        for p in a.attendee_products:
            if p.product.category == 'patreon':
                patreon = True
                subtotal = 0
            elif not patreon:
                subtotal += p.product.price * p.quantity
        if not patreon:
            total += subtotal

    return _get_discounted_price(total, discount_value) + application.credit


def _calculate_price(
    products: List[Product],
    products_data: dict[int, PaymentProduct],
    discount_value: float,
    application: Application,
    already_patreon: bool,
    edit_passes: bool,
) -> float:
    credit = _get_credit(application, discount_value) if edit_passes else 0
    logger.info('Credit: %s', credit)
    attendees = {}
    for p in products:
        quantity = products_data[p.id].quantity
        attendee_id = products_data[p.id].attendee_id
        if attendee_id not in attendees:
            attendees[attendee_id] = {'standard': 0, 'supporter': 0, 'patreon': 0}

        if attendees[attendee_id]['patreon'] > 0:
            continue

        if p.category == 'patreon':
            attendees[attendee_id]['patreon'] = (
                p.price * quantity if not already_patreon else 0
            )
            attendees[attendee_id]['standard'] = 0
            attendees[attendee_id]['supporter'] = 0
        elif p.category == 'supporter':
            attendees[attendee_id]['supporter'] += p.price * quantity
        else:
            attendees[attendee_id]['standard'] += p.price * quantity

    standard_amount = sum(a['standard'] for a in attendees.values())
    supporter_amount = sum(a['supporter'] for a in attendees.values())
    patreon_amount = sum(a['patreon'] for a in attendees.values())

    logger.info('Standard amount: %s', standard_amount)
    logger.info('Supporter amount: %s', supporter_amount)
    logger.info('Patreon amount: %s', patreon_amount)

    if standard_amount > 0:
        standard_amount = _get_discounted_price(standard_amount, discount_value)
    standard_amount = standard_amount - credit

    return standard_amount + supporter_amount + patreon_amount


def create_payment(
    db: Session,
    obj: schemas.PaymentCreate,
    user: TokenData,
) -> InternalPaymentCreate:
    application = application_crud.get(db, obj.application_id, user)
    if application.status != ApplicationStatus.ACCEPTED.value:
        raise HTTPException(status_code=400, detail='Application is not accepted')

    if not (simplefi_api_key := application.popup_city.simplefi_api_key):
        raise HTTPException(
            status_code=400, detail='Popup city does not have a Simplefi API key'
        )

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
    already_patreon = any(p.category == 'patreon' for p in application_products)
    is_buying_patreon = any(p.category == 'patreon' for p in products)

    if obj.edit_passes and is_buying_patreon and not already_patreon:
        logger.error('Cannot edit passes for Patreon products')
        raise HTTPException(
            status_code=400,
            detail='Cannot edit passes for Patreon products',
        )

    response = InternalPaymentCreate(
        products=obj.products,
        application_id=application.id,
        currency='USD',
    )

    discount_assigned = application.discount_assigned or 0

    response.amount = _calculate_price(
        products,
        products_data,
        discount_value=discount_assigned,
        application=application,
        already_patreon=already_patreon,
        edit_passes=obj.edit_passes,
    )

    group = application.citizen.get_group(application.popup_city_id)
    if group:
        discounted_amount = _calculate_price(
            products,
            products_data,
            discount_value=group.discount_percentage,
        )
        if discounted_amount < response.amount:
            response.amount = discounted_amount
            response.group_id = group.id

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
            application=application,
            already_patreon=already_patreon,
            edit_passes=obj.edit_passes,
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

    payment_request = simplefi.create_payment(
        response.amount,
        reference=reference,
        simplefi_api_key=simplefi_api_key,
    )

    response.external_id = payment_request['id']
    response.status = payment_request['status']
    response.checkout_url = payment_request['checkout_url']

    return response
