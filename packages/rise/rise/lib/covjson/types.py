# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, TypedDict

"""
All of these typeddicts are used for type hinting the result of 
a pydantic model dump. They are thus not used for validation and
just for dev ux. They are prefixed with _Dict to distinguish them
from the pydantic models of the same name
"""


class ParameterDict(TypedDict):
    type: str
    description: dict[str, str]
    unit: dict
    observedProperty: dict


class CoverageRangeDict(TypedDict):
    type: Literal["NdArray"]
    dataType: Literal["float"]
    axisNames: list[str]
    shape: list[int]
    values: list[float | None]


class CoverageDict(TypedDict):
    type: Literal["Coverage"]
    domain: dict
    ranges: dict[str, CoverageRangeDict]
    domainType: Literal["PolygonSeries", "PointSeries"]


class CoverageCollectionDict(TypedDict):
    type: str
    parameters: dict[str, ParameterDict]
    referencing: list
    coverages: list[CoverageDict]
