from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class SubscriptionBase(BaseModel):
    
    name: str = Field(..., min_length=2, max_length=100, description="Название сервиса")
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Цена подписки")
    currency: str = Field("RUB", max_length=3)
    payment_date: int = Field(..., description="День списания (1-31)")
    is_active: bool = True
    
    @field_validator('payment_date')
    @classmethod
    def validate_day(cls, v: int) -> int:
        if not (1 <= v <= 31):
            raise ValueError('Day must be between 1 and 31')
        return v
    
class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_date: Optional[int] = None
    is_active: Optional[bool] = None
    

class SubscriptionRead(SubscriptionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)