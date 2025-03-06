# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from enum import Enum, auto
from typing import Literal, Optional, TypedDict
from pydantic import BaseModel




class CatalogItemEndpointResponseDataAttributes(TypedDict):
    _id: str
    itemTitle: str
    itemDescription: str
    itemRecordStatusId: int
    isModeled: bool
    hasProfile: bool
    itemType: dict
    parameterId: Optional[str]
    parameterName: Optional[str]
    parameterUnit: Optional[str]
    parameterTimestep: Optional[str]
    parameterTransformation: Optional[str]


class CatalogItemResponseData(TypedDict):
    id: str
    type: Literal["CatalogItem"]
    attributes: CatalogItemEndpointResponseDataAttributes

    # only have this key in here if it is coming from the catalog endpoint
    results: dict


class CatalogItemsResponse(TypedDict):
    # we can't do a union of typeddicts so we have to settle for this
    data: dict | list



class GeoJsonResponse(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[
        dict[
            Literal["type", "id", "properties"],
            Literal["Feature"],
        ]
    ]


JsonPayload = dict
Url = str


class ZType(Enum):
    SINGLE = auto()
    # Every value between two values
    RANGE = auto()
    # An enumerated list that the value must be in
    ENUMERATED_LIST = auto()


class Parameter(TypedDict):
    type: str
    description: dict[str, dict]
    unit: dict
    observedProperty: dict


class CoverageRange(TypedDict):
    type: Literal["NdArray"]
    dataType: Literal["float"]
    axisNames: list[str]
    shape: list[int]
    values: list[float]


class Coverage(TypedDict):
    type: Literal["Coverage"]
    domain: dict
    ranges: dict[str, CoverageRange]
    domainType: Literal["PolygonSeries", "PointSeries"]


class CoverageCollection(TypedDict):
    type: str
    parameters: dict[str, Parameter]
    referencing: list
    coverages: list[Coverage]
