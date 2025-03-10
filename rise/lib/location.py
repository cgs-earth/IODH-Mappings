# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
from copy import deepcopy
from datetime import datetime
import json
import logging
from typing import Literal, Optional, assert_never
from pydantic import BaseModel, field_validator
import shapely
import shapely.wkt
from rise.lib.cache import RISECache
from rise.lib.helpers import (
    get_trailing_id,
    merge_pages,
    parse_bbox,
    parse_date,
    parse_z,
    safe_run_async,
)
from rise.lib.types.helpers import ZType
from rise.lib.types.includes import LocationIncluded
from rise.lib.types.location import LocationData, PageLinks


LOGGER = logging.getLogger()


class LocationResponse(BaseModel):
    """
    This class represents the top level location/ response that is returned from the API
    It is validated with pydantic on initialization and multiple methods are added to it to make it easier to manipulate data
    """

    # links and pagination may not be present if there is only one location
    links: Optional[PageLinks] = None
    meta: Optional[
        dict[
            Literal["totalItems", "itemsPerPage", "currentPage"],
            int,
        ]
    ] = None
    # data represents the list of locations returned
    data: list[LocationData]

    @classmethod
    def from_api_pages(cls, pages: dict[str, dict]):
        return cls(**merge_pages(pages))

    @field_validator("data", check_fields=True, mode="before")
    @classmethod
    def ensure_list(cls, data: LocationData | list[LocationData]) -> list[LocationData]:
        """
        Data can be a list of dicts or just a dict if there is only one location;
        make sure it is always a list for consistency
        """
        if not isinstance(data, list):
            return [data]
        return data

    def filter_by_date(self, datetime_: str):
        """
        Filter a list of locations by date
        """
        if not self.data[0].attributes:
            raise RuntimeError("Can't filter by date")

        filteredResp = self.copy(deep=True)

        parsed_date: list[datetime] = parse_date(datetime_)

        if len(parsed_date) == 2:
            start, end = parsed_date

            for i, location in enumerate(filteredResp.data):
                updateDate = datetime.fromisoformat(location.attributes.updateDate)
                if updateDate < start or updateDate > end:
                    filteredResp.data.pop(i)

        elif len(parsed_date) == 1:
            parsed_date_str = str(parsed_date[0])
            filteredResp.data = [
                location
                for location in filteredResp.data
                if location.attributes.updateDate.startswith(parsed_date_str)
            ]

        else:
            raise RuntimeError(
                "datetime_ must be a date or date range with two dates separated by '/' but got {}".format(
                    datetime_
                )
            )

        return filteredResp

    def _filter_by_geometry(
        self,
        geometry: Optional[shapely.geometry.base.BaseGeometry],
        # Vertical level
        z: Optional[str] = None,
    ):
        # need to deep copy so we don't change the dict object
        copy_to_return = deepcopy(self)
        indices_to_pop = set()
        parsed_z = parse_z(str(z)) if z else None

        for i, v in enumerate(self.data):
            elevation = v.attributes.elevation

            if elevation is None:
                indices_to_pop.add(i)
                continue

            if parsed_z:
                match parsed_z:
                    case [ZType.RANGE, x]:
                        if elevation < x[0] or elevation > x[1]:
                            indices_to_pop.add(i)
                    case [ZType.SINGLE, x]:
                        if elevation != x[0]:
                            indices_to_pop.add(i)
                    case [ZType.ENUMERATED_LIST, x]:
                        if elevation not in x:
                            indices_to_pop.add(i)
                    case _:
                        assert_never(parsed_z)

            if geometry:
                result_geo = shapely.geometry.shape(
                    # need to convert the pydantic model to a simple
                    # dict to use shapely with it
                    v.attributes.locationCoordinates.model_dump()
                )

                if not geometry.contains(result_geo):
                    indices_to_pop.add(i)

        # by reversing the list we pop from the end so the
        # indices will be in the correct even after removing items
        for i in sorted(indices_to_pop, reverse=True):
            copy_to_return.data.pop(i)

        return copy_to_return

    def filter_by_wkt(
        self,
        wkt: Optional[str] = None,
        z: Optional[str] = None,
    ):
        """Filter a location by the well-known-text geometry representation"""
        parsed_geo = shapely.wkt.loads(str(wkt)) if wkt else None
        return self._filter_by_geometry(parsed_geo, z)

    def drop_location(self, location_id: int):
        """Given a location id, drop all all data that is associated with that location"""
        new = self.model_copy()

        filtered_locations = [
            loc for loc in new.data if loc.attributes.id != location_id
        ]

        new.data = filtered_locations

        return new

    def filter_by_bbox(
        self,
        bbox: Optional[list] = None,
        z: Optional[str] = None,
    ):
        if bbox:
            parse_result = parse_bbox(bbox)
            shapely_box = parse_result[0] if parse_result else None
            z = parse_result[1] if parse_result else z

        shapely_box = parse_bbox(bbox)[0] if bbox else None
        # TODO what happens if they specify both a bbox with z and a z value?
        z = parse_bbox(bbox)[1] if bbox else z

        return self._filter_by_geometry(shapely_box, z)

    def filter_by_limit(self, limit: int):
        self.data = self.data[:limit]
        return self

    def remove_before_offset(self, offset: int):
        self.data = self.data[offset:]
        return self

    def filter_by_id(
        self,
        identifier: Optional[str] = None,
    ):
        self.data = [
            location
            for location in self.data
            if str(location.attributes.id) == identifier
        ]
        return self

    def to_geojson(self, single_feature: bool = False) -> dict:
        features = []

        for location_feature in self.data:
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
                "id": location_feature.attributes.id,
                "properties": {
                    "Locations@iot.count": 1,
                    "name": location_feature.attributes.locationName,
                    "id": location_feature.attributes.id,
                    "Locations": [
                        {
                            "location": location_feature.attributes.locationCoordinates.model_dump()
                        }
                    ],
                },
                "geometry": location_feature.attributes.locationCoordinates.model_dump(),
            }
            features.append(feature_as_geojson)
            if single_feature:
                return feature_as_geojson

        return {"type": "FeatureCollection", "features": features}

    def get_results(
        self, catalogItemEndpoints: list[str], cache: RISECache
    ) -> dict[str, str]:
        result_endpoints = [
            f"https://data.usbr.gov/rise/api/result?page=1&itemsPerPage=25&itemId={get_trailing_id(endpoint)}"
            for endpoint in catalogItemEndpoints
        ]

        fetched_result = safe_run_async(cache.get_or_fetch_group(result_endpoints))

        return fetched_result


class LocationResponseWithIncluded(LocationResponse):
    # included represents the additional data that is explicitly requested in the fetch request
    included: list[LocationIncluded]

    def get_catalogItemURLs(self) -> dict[str, list[str]]:
        """Get all catalog items associated with a particular location"""
        locationIdToCatalogRecord: dict[str, str] = {}

        catalogRecordToCatalogItems: dict[str, list[str]] = {}

        for included_item in self.included:
            if included_item.type == "CatalogRecord":
                catalogRecord = included_item.id
                locationId = included_item.relationships.location
                assert locationId is not None
                locationId = locationId.data[0]["id"]
                locationIdToCatalogRecord[locationId] = catalogRecord
            elif included_item.type == "CatalogItem":
                catalogItem = included_item.id
                catalogRecord = included_item.relationships.catalogRecord
                assert catalogRecord is not None
                catalogRecord = catalogRecord.data[0]["id"]
                if catalogRecord not in catalogRecordToCatalogItems:
                    catalogRecordToCatalogItems[catalogRecord] = []
                catalogRecordToCatalogItems[catalogRecord].append(catalogItem)

        join: dict[str, list[str]] = {}
        for locationId, catalogRecord in locationIdToCatalogRecord.items():
            if catalogRecord in catalogRecordToCatalogItems:
                for catalogItem in catalogRecordToCatalogItems[catalogRecord]:
                    catalogItemURL = f"https://data.usbr.gov{catalogItem}"
                    if locationId not in join:
                        join[str(locationId)] = [catalogItemURL]
                    else:
                        join[locationId].append(catalogItemURL)

        return join

    def get_parameters(
        self,
        cache: RISECache,
    ) -> dict[str, list[str | None]]:
        locationsToCatalogItemURLs = self.get_catalogItemURLs()

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

    def filter_by_properties(
        self, select_properties: list[str] | str, cache: RISECache
    ):
        """Filter a location by a list of properties. NOTE you can also do this directly in RISE. Make sure you actually need this and can't fetch up front."""
        list_of_properties: list[str] = (
            [select_properties]
            if isinstance(select_properties, str)
            else select_properties
        )

        response = self
        locationsToParams = self.get_parameters(cache)
        for param in list_of_properties:
            for location, paramList in locationsToParams.items():
                if param not in paramList:
                    response = self.drop_location(int(location))

        return response
