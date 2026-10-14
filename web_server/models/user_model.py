import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    password: str
    role: str = Field(index=True)
    last_login: datetime.datetime = Field(default_factory=datetime.datetime.now)
    status: bool = Field(default=True)

