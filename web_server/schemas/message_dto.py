from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SendMessagePayload(BaseModel):
    content: str
    restricted_from_surveillance: Optional[bool] = False
