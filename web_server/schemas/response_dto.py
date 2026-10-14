from pydantic import BaseModel, ConfigDict
from typing import Any, Optional

class ResponseDTO(BaseModel):
    message: str
    object: Optional[Any]
    status: bool