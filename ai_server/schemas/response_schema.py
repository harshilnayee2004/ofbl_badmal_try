from typing import Optional, Any

from pydantic import BaseModel


class ResponseDTO(BaseModel):
    message: str
    status: bool
    object: Optional[Any]