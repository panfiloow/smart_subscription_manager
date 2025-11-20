from pydantic import BaseModel, ConfigDict, EmailStr
import uuid
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
