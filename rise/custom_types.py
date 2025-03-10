# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, Optional, TypedDict


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
