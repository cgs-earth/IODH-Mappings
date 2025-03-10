# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, Optional, Union
from pydantic import BaseModel, Field

from rise.lib.types.location import PointCoordinates, PolygonCoordinates

class LocationDataAttributes(BaseModel):
    """ 
    The `attributes:` key within each `data:` key for location/ 
    Thus, located at the following nesting:
        data:
            attributes:
    """

    # We use an alias here to map the _id field to the id field since the _ in the name causes issues
    # https://stackoverflow.com/questions/59562997/how-to-parse-and-read-id-field-from-and-to-a-pydantic-model
    id: int = Field(..., alias="_id")

    locationName: str
    locationDescription: Optional[str]
    locationStatusId: int
    # the "type" field tells us whether to validate as a Point or a Polygon
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

    relationships: dict[Literal["relationships"], 
                        dict[Literal["catalogItems"], list[str]]]


class LocationDataWithResults(BaseModel):
    """the `data:` key of the location response"""
    id: str
    type: Literal["Location"]
    attributes: LocationDataAttributes
