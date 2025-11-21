from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"


class SubscriptionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Название сервиса")
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Цена подписки")
    currency: Currency = Field(default=Currency.RUB, description="Валюта подписки")
    payment_date: int = Field(..., description="День списания (1-31)")
    is_active: bool = True

    @field_validator("payment_date")
    @classmethod
    def validate_day(cls, v: int) -> int:
        if not (1 <= v <= 31):
            raise ValueError("Day must be between 1 and 31")
        return v


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[Currency] = None
    payment_date: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("payment_date")
    @classmethod
    def validate_day(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (1 <= v <= 31):
            raise ValueError("Day must be between 1 and 31")
        return v


class SubscriptionRead(SubscriptionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AnalyticsResponse(BaseModel):
    total_monthly_price: Decimal = Field(..., description="Общая сумма в базовой валюте (RUB)")
    details: Dict[Currency, Decimal] = Field(..., description="Детализация по валютам")