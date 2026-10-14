from pydantic import BaseModel

class InferenceSchema(BaseModel):
    prompt: str
    image: str
