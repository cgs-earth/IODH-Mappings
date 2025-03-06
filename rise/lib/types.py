
from pydantic import BaseModel, Field, FiniteFloat
from typing import Literal, Optional, Union



class PointCoordinates(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[FiniteFloat, FiniteFloat]  # Expecting exactly two values: [longitude, latitude]

class PolygonCoordinates(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[FiniteFloat]]]  # A list of linear rings (each ring is a list of [longitude, latitude] pairs)

class LocationDataAttributes(BaseModel):
    _id: int
    locationName: str
    locationDescription: Optional[str]
    locationStatusId: int
    locationCoordinates:  Union[PointCoordinates, PolygonCoordinates] = Field(discriminator="type")
    elevation: Optional[str]
    createDate: str
    updateDate: str
    horizontalDatum: dict
    locationGeometry: dict
    locationTags: list[dict]
    relatedLocationIds: Optional[str]
    projectNames: list[str]
    locationTypeName: str
    locationRegionNames: list[str]
    locationUnifiedRegionNames: list[str]

class RelationshipData(BaseModel):
    data: list[dict[Literal["id", "type"], str]]

class LocationDataRelationships(BaseModel):
    states: dict
    locationUnifiedRegions: RelationshipData
    catalogRecords: RelationshipData


class LocationData(BaseModel):
    id: str
    type: Literal["Location"]
    attributes: LocationDataAttributes
    relationships: LocationDataRelationships

class LocationIncluded(BaseModel):
    id: str
    type: str
    relationships: dict[str, dict]
