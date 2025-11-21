from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import crud_subscription
import uuid
from app.schemas.subscription import Currency 

# Хардкод курсов (потом заменим на Redis/API)
EXCHANGE_RATES = {
    Currency.RUB: Decimal("1.0"),
    Currency.USD: Decimal("100.0"),
    Currency.EUR: Decimal("110.0"),
    Currency.KZT: Decimal("0.2")
}

async def calculate_expenses(db: AsyncSession, user_id: uuid.UUID) -> dict:
    raw_totals = await crud_subscription.subscription.get_total_cost_by_currency(
        db, user_id=user_id
    )

    final_total_rub = Decimal("0.0")
    details = {}

    for currency_str, total_amount in raw_totals:
        amount = total_amount if total_amount else Decimal("0.0")
        
        try:
            currency_enum = Currency(currency_str)
        except ValueError:
            currency_enum = Currency.RUB

        details[currency_enum] = amount

        rate = EXCHANGE_RATES.get(currency_enum, Decimal("1.0"))
        final_total_rub += amount * rate

    return {
        "total_monthly_price": final_total_rub.quantize(Decimal("1.00")),
        "details": details
    }