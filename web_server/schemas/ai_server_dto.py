from typing import Optional

from pydantic import BaseModel


class AiServerG70BoxRequest(BaseModel):
    box_id:int
    result:str
    sequence_number:int
    message:str

class AiServerM104BoxRequest(BaseModel):
    box_id:int
    result:bool
    sequence_no:int
    message:str