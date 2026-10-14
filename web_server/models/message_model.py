from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    sender_id: int = Field(index=True)
    receiver_id: Optional[int] = Field(default=None, index=True)
    content: str
    restricted_from_surveillance: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.now)
    is_read: bool = Field(default=False)
