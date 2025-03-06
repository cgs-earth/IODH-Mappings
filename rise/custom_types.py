# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from enum import Enum, auto
from typing import Literal, Optional, TypedDict


class EDRQuery(TypedDict):
    data_queries: list[dict]


class LocationDataCoordinates(TypedDict):
    type: Literal["Point", "Polygon"]
    coordinates: list[float]


class LocationDataAttributes(TypedDict):
    _id: int
    locationParentId: Optional[str]
    locationName: str
    locationDescription: str
    locationStatusId: int
    locationCoordinates: LocationDataCoordinates
    elevation: Optional[str]
    createDate: str
    updateDate: str
    horizontalDatum: dict
    locationGeometry: dict
    verticalDatum: str
    locationTags: list[dict]
    relatedLocationIds: Optional[str]
    projectNames: list[str]
    locationTypeName: str
    locationRegionNames: list[str]
    locationUnifiedRegionNames: list[str]


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


class LocationDataRelationships(TypedDict):
    states: dict
    locationUnifiedRegions: dict
    catalogRecords: dict
    catalogItems: CatalogItemsResponse


class LocationData(TypedDict):
    id: str
    type: Literal["Location"]
    attributes: LocationDataAttributes
    relationships: LocationDataRelationships


class LocationIncluded(TypedDict):
    id: str
    type: str
    relationships: dict[str, dict]

class LocationResponse(TypedDict):
    links: dict[Literal["self", "first", "last", "next"], str]
    meta: dict[
        Literal["totalItems", "itemsPerPage", "currentPage"],
        int,
    ]
    included: list[LocationIncluded]
    data: list[LocationData]


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
