# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, FiniteFloat
from rise.lib.types.includes import RelationshipData


class PointCoordinates(BaseModel):
    type: Literal["Point"]
    coordinates: tuple[
        FiniteFloat, FiniteFloat
    ]  # Expecting exactly two values: [longitude, latitude]


class PolygonCoordinates(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[
        list[list[FiniteFloat]]
    ]  # A list of linear rings (each ring is a list of [longitude, latitude] pairs)


class LocationDataAttributes(BaseModel):
    # We use an alias here to map the _id field to the id field since the _ in the name causes issues
    # https://stackoverflow.com/questions/59562997/how-to-parse-and-read-id-field-from-and-to-a-pydantic-model
    id: int = Field(..., alias='_id')
    locationName: str
    locationDescription: Optional[str]
    locationStatusId: int
    locationCoordinates: Union[PointCoordinates, PolygonCoordinates] = Field(
        discriminator="type"
    )
    elevation: Optional[int]
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


class LocationDataRelationships(BaseModel):
    states: dict
    locationUnifiedRegions: RelationshipData
    catalogRecords: RelationshipData


class LocationData(BaseModel):
    id: str
    type: Literal["Location"]
    attributes: LocationDataAttributes
