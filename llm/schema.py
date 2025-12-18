from pydantic import BaseModel, Field
from typing import List

class HeadlineExtraction(BaseModel):
    headlines: List[str] = Field(
        ..., 
        min_items=3, 
        max_items=10,
        description="List of news headlines"
    )
