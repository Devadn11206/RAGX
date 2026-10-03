from pydantic import BaseModel, Field
from typing import List, Optional

VALID_ENTITY_TYPES = {
    "PERSON", "ORGANIZATION", "COMPANY", "PRODUCT", "LOCATION", 
    "EVENT", "DATE", "TECHNOLOGY", "PROJECT", "CONCEPT"
}

VALID_RELATION_TYPES = {
    "WORKS_FOR", "FOUNDED", "CREATED", "DEVELOPED", "LOCATED_IN", 
    "PART_OF", "USES", "OWNS", "ACQUIRED", "MANAGES", 
    "PARTICIPATED_IN", "RELATED_TO", "DEPENDS_ON", "OCCURRED_IN"
}

class ExtractedEntity(BaseModel):
    name: str = Field(description="The name of the entity")
    type: str = Field(description="The type of the entity. Must be one of the predefined types.")

class ExtractedRelation(BaseModel):
    source: str = Field(description="The source entity name")
    relation_type: str = Field(description="The type of the relation. Must be one of the predefined types.")
    target: str = Field(description="The target entity name")
    evidence: str = Field(description="A short quote from the text that proves this relationship")

class ExtractionResult(BaseModel):
    entities: List[ExtractedEntity] = []
    relations: List[ExtractedRelation] = []
