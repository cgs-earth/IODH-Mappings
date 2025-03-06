from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


class RelationshipData(BaseModel):
    data: list[dict[Literal["id", "type"], str]]

    @field_validator("data", check_fields=True, mode="before")
    @classmethod
    def ensure_list(cls, data):
        if not isinstance(data, list):
            return [data]
        return data


class IncludeRelationships(BaseModel):
    catalogRecord: Optional[RelationshipData] = None
    location: Optional[RelationshipData] = None
    catalogItems: Optional[RelationshipData] = None
    parameter: Optional[RelationshipData] = None


class LocationIncluded(BaseModel):
    id: str
    attributes: dict
    type: Literal["CatalogRecord", "Location", "CatalogItem"]
    relationships: IncludeRelationships = Field(default_factory=IncludeRelationships)
