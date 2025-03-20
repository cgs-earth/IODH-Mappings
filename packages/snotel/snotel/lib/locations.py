# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from com.cache import RedisCache
from rise.lib.helpers import await_
from snotel.lib.types import StationDTO


@dataclass
class LocationCollection:
    locations: list[StationDTO]

    def drop_all_locations_but_id(self, location_id: str):
        return LocationCollection(
            locations=[loc for loc in self.locations if loc.stationId == location_id]
        )

    def drop_outside_of_geometry(self, geometry):
        # Placeholder for future implementation
        return self


def get_locations():
    cache = RedisCache()
    result = await_(
        cache.get_or_fetch(
            "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true"
        )
    )
    locations = [StationDTO.model_validate(res) for res in result]
    return LocationCollection(locations=locations)
