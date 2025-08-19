# extractor/schema.py
from pydantic import BaseModel
from typing import List, Optional

class SourceInfo(BaseModel):
    page: int
    bbox: List[int]  # [x1,y1,x2,y2]

class LineItem(BaseModel):
    description: str
    quantity: Optional[float]
    unit_price: Optional[float]
    amount: Optional[float]
    source: Optional[SourceInfo]
    confidence: float

class Field(BaseModel):
    name: str
    value: Optional[str]
    confidence: float
    source: Optional[SourceInfo]

class ExtractionResult(BaseModel):
    doc_type: str
    fields: List[Field]
    line_items: Optional[List[LineItem]]
    overall_confidence: float
    qa: dict
