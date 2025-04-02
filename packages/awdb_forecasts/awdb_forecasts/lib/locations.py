# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from awdb_com.locations import LocationCollection
from com.helpers import EDRFieldsMapping
from rise.lib.covjson.types import CoverageCollectionDict
from typing import Optional

type longitudeAndLatitude = tuple[float, float]


class ForecastLocationCollection(LocationCollection):
    def __init__(self, locations: list) -> None:
        super().__init__(locations)

    def to_covjson(
        self,
        fieldMapper: EDRFieldsMapping,
        datetime_: Optional[str],
        select_properties: Optional[list[str]],
    ) -> CoverageCollectionDict: ...
