# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from awdb_com.locations import LocationCollection
from com.helpers import (
    EDRFieldsMapping,
)
from rise.lib.covjson.types import CoverageCollectionDict
from snotel.lib.covjson_builder import CovjsonBuilder
from typing import Optional, cast

type longitudeAndLatitude = tuple[float, float]


class SnotelLocationCollection(LocationCollection):
    """A wrapper class containing locations and methods to filter them"""

    def __init__(self, select_properties: Optional[list[str]] = None):
        super().__init__(select_properties)

    def to_covjson(
        self,
        fieldMapper: EDRFieldsMapping,
        datetime_: Optional[str],
        select_properties: Optional[list[str]],
    ) -> CoverageCollectionDict:
        stationTriples: list[str] = [
            location.stationTriplet
            for location in self.locations
            if location.stationTriplet
        ]

        tripleToGeometry: dict[str, longitudeAndLatitude] = {}
        for location in self.locations:
            if location.stationTriplet and location.longitude and location.latitude:
                assert location.longitude and location.latitude
                tripleToGeometry[location.stationTriplet] = (
                    location.longitude,
                    location.latitude,
                )

        # We cast the return value here because we know it will be a CoverageCollectionDict
        covjson_result = CovjsonBuilder(
            stationTriples, tripleToGeometry, fieldMapper, datetime_, select_properties
        ).render()

        return cast(
            CoverageCollectionDict,
            covjson_result,
        )
