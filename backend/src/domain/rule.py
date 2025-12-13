from pydantic import BaseModel

class Rule(BaseModel):
    id: int | None = None
    pattern: str
    category: str
