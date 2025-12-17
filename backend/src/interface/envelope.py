from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standardized API response envelope.
    Follows: { "data": {...}, "meta": {...}, "errors": [...] }
    """
    model_config = ConfigDict(strict=True)

    data: Optional[T] = None
    meta: dict = {}
    errors: List[str] = []

    @classmethod
    def success(cls, data: T, meta: dict = None) -> "ResponseEnvelope[T]":
        return cls(data=data, meta=meta or {})

    @classmethod
    def error(cls, message: str) -> "ResponseEnvelope[T]":
        return cls(errors=[message])
