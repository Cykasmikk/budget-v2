from pydantic import BaseModel, ConfigDict
from typing import Optional

class Rule(BaseModel):
    """
    Represents a categorization rule.
    Maps a regex pattern to a category.
    
    Attributes:
        id (Optional[int]): Unique identifier for the rule.
        pattern (str): Regex pattern to match description.
        category (str): Category to assign if matched.
        tenant_id (Optional[str]): The tenant this rule belongs to.
    """
    model_config = ConfigDict(strict=True)
    id: Optional[int] = None
    pattern: str
    category: str
    tenant_id: Optional[str] = None # UUID string

