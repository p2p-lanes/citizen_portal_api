from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.applications.crud import application as application_crud
from app.api.applications.schemas import ApplicationStatus, TicketCategory
from app.api.payments import schemas
from app.api.payments.schemas import InternalPaymentCreate
from app.api.products.crud import product as product_crud
from app.api.products.models import Product
from app.api.products.schemas import ProductFilter
from app.core import simplefi
from app.core.security import TokenData


def _get_price(product: Product, discount_assigned: int) -> float:
    return round(product.price * (1 - discount_assigned / 100), 2)


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

    ticket_category = application.ticket_category
    discount_assigned = (
        application.discount_assigned
        if ticket_category == TicketCategory.DISCOUNTED.value
        else 0
    )

    if patreon := next((p for p in products if p.category == 'patreon'), None):
        amount = _get_price(patreon, discount_assigned=0)
    else:
        amounts = {}
        for p in products:
            pdata = products_data[p.id]
            attendee_id = pdata.attendee_id
            _amount = _get_price(p, discount_assigned) * pdata.quantity
            amounts[attendee_id] = (
                _amount + amounts.get(attendee_id, 0)
                if p.category != 'supporter'
                else _get_price(p, discount_assigned=0)
            )
        amount = sum(amounts.values())

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
