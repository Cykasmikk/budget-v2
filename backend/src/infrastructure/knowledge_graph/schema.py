from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class NodeType(str, Enum):
    MERCHANT = "Merchant"
    CATEGORY = "Category"
    PROJECT = "Project"
    RULE = "Rule"
    TRANSACTION = "Transaction"

class EdgeType(str, Enum):
    BELONGS_TO = "BELONGS_TO"       # Transaction -> Category / Project
    SIMILAR_TO = "SIMILAR_TO"       # Merchant -> Merchant
    CONFLICTS_WITH = "CONFLICTS_WITH" # Rule -> Rule
    PRECEDES = "PRECEDES"           # Transaction -> Transaction (Chronological)
    PART_OF = "PART_OF"             # Transaction -> Merchant

class Node(BaseModel):
    id: str
    type: NodeType
    properties: Dict[str, Any] = {}
    
    model_config = ConfigDict(frozen=True)

class Edge(BaseModel):
    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = {}

    model_config = ConfigDict(frozen=True)
