# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from copy import deepcopy
import json
import logging
from typing import Optional
import shapely.wkt

import shapely  

from pygeoapi.provider.base import (
    ProviderQueryError,
)
import asyncio

from rise.custom_types import (
    JsonPayload,
    Url,
)
from rise.lib.cache import RISECache
from rise.lib.helpers import parse_bbox, safe_run_async
from rise.lib.location import LocationResponse


LOGGER = logging.getLogger(__name__)


locationId = str
catalogItemEndpoint = str


class LocationHelper:
    locationId = str
    paramIdList = list[str | None]

    @staticmethod
    def get_parameters(
        allLocations: LocationResponse,
        cache: RISECache,
    ) -> dict[locationId, paramIdList]:
        locationsToCatalogItemURLs = LocationHelper.get_catalogItemURLs(allLocations)

        locationToParams: dict[str, list[str | None]] = {}

        async def get_all_params_for_location(location, catalogItems):
            # Map a location to a list of catalog item responses
            urlItemMapper: dict[str, dict] = await cache.get_or_fetch_group(
                catalogItems
            )

            try:
                allParams = []

                for item in urlItemMapper.values():
                    if item is not None:
                        res = CatalogItem.get_parameter(item)
                        if res is not None:
                            allParams.append(res["id"])

            except KeyError:
                with open("rise/tests/data/debug.json", "w") as f:
                    json.dump(urlItemMapper, f)
                raise ProviderQueryError("Could not get parameters")

            # drop all empty params
            allParams = list(filter(lambda x: x is not None, allParams))
            return location, allParams

        async def gather_parameters():
            """Asynchronously fetch all parameters for all locations"""
            tasks = [
                get_all_params_for_location(location, catalogItemURLs)
                for location, catalogItemURLs in locationsToCatalogItemURLs.items()
            ]
            results = await asyncio.gather(*tasks)
            return {location: params for location, params in results}

        locationToParams = safe_run_async(gather_parameters())

        # should have the same number of locations in each
        assert len(locationToParams) == len(locationsToCatalogItemURLs)
        return locationToParams



    @staticmethod
    def filter_by_limit(
        location_response: LocationResponse, limit: int, inplace: bool = False
    ) -> LocationResponse:
        if not inplace:
            location_response = deepcopy(location_response)
        location_response["data"] = location_response["data"][:limit]
        return location_response

    @staticmethod
    def remove_before_offset(
        location_response: LocationResponse, offset: int, inplace: bool = False
    ):
        if not inplace:
            location_response = deepcopy(location_response)
        location_response["data"] = location_response["data"][offset:]
        return location_response

    @staticmethod
    def filter_by_id(
        location_response: LocationResponse,
        identifier: Optional[str] = None,
        inplace: bool = False,
    ) -> LocationResponse:
        if not inplace:
            location_response = deepcopy(location_response)
        location_response["data"] = [
            location
            for location in location_response["data"]
            if str(location["attributes"]["_id"]) == identifier
        ]
        return location_response

    @staticmethod
    def to_geojson(
        location_response: LocationResponse, single_feature: bool = False
    ) -> dict:
        features = []

        if type(location_response["data"]) is not list:
            location_response["data"] = [location_response["data"]]

        for location_feature in location_response["data"]:
            # z = location_feature["attributes"]["elevation"]
            # if z is not None:
            #     location_feature["attributes"]["locationCoordinates"][
            #         "coordinates"
            #     ].append(float(z))
            #     LOGGER.error(
            #         location_feature["attributes"]["locationCoordinates"]["coordinates"]
            #     )

            feature_as_geojson = {
                "type": "Feature",
                "id": location_feature["attributes"]["_id"],
                "properties": {
                    "Locations@iot.count": 1,
                    "name": location_feature["attributes"]["locationName"],
                    "id": location_feature["attributes"]["_id"],
                    "Locations": [
                        {
                            "location": location_feature["attributes"][
                                "locationCoordinates"
                            ]
                        }
                    ],
                },
                "geometry": location_feature["attributes"]["locationCoordinates"],
            }
            features.append(feature_as_geojson)
            if single_feature:
                return feature_as_geojson

        return {"type": "FeatureCollection", "features": features}

    @staticmethod
    def get_results(
        catalogItemEndpoints: list[str], cache: RISECache
    ) -> dict[Url, JsonPayload]:
        result_endpoints = [
            f"https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=25&itemId={get_trailing_id(endpoint)}"
            for endpoint in catalogItemEndpoints
        ]

        fetched_result = safe_run_async(cache.get_or_fetch_group(result_endpoints))

        return fetched_result


class CatalogItem:
    @classmethod
    def get_parameter(cls, data: dict) -> dict[str, str] | None:
        try:
            parameterName = data["data"]["attributes"]["parameterName"]
            if not parameterName:
                return None

            id = data["data"]["attributes"]["parameterId"]
            # NOTE id is returned as an int but needs to be a string in order to query it
            return {"id": str(id), "name": parameterName}
        except KeyError:
            LOGGER.error(f"Could not find a parameter in {data}")
            return None
