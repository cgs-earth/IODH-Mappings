# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from copy import deepcopy
from datetime import datetime
import logging
from typing import Literal, NewType, Optional, assert_never
from pydantic import BaseModel, field_validator
import shapely
import shapely.wkt
from rise.lib.cache import RISECache
from rise.lib.helpers import parse_bbox, parse_date, parse_z
from rise.lib.types.helpers import ZType
from rise.lib.types.includes import LocationIncluded
from rise.lib.types.location import LocationData

CatalogItem = NewType("CatalogItem", str)

LOGGER = logging.getLogger()

class LocationResponse(BaseModel):
    links: Optional[dict[Literal["self", "first", "last", "next"], str]] = None
    meta: Optional[
        dict[
            Literal["totalItems", "itemsPerPage", "currentPage"],
            int,
        ]
    ] = None
    included: list[LocationIncluded]
    data: list[LocationData]

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

    def get_catalogItemURLs(self) -> dict[str, list[CatalogItem]]:
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

        join: dict[str, list[CatalogItem]] = {}
        for locationId, catalogRecord in locationIdToCatalogRecord.items():
            if catalogRecord in catalogRecordToCatalogItems:
                for catalogItem in catalogRecordToCatalogItems[catalogRecord]:
                    catalogItemURL = f"https://data.usbr.gov{catalogItem}"
                    if locationId not in join:
                        join[str(locationId)] = [CatalogItem(catalogItemURL)]
                    else:
                        join[locationId].append(CatalogItem(catalogItemURL))

        return join


    def filter_by_date(
        self, datetime_: str
    ):
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
                updateDate = datetime.fromisoformat(
                    location.attributes.updateDate
                )
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
    
    def filter_by_properties(
        self, select_properties: list[str] | str, cache: RISECache
    ):
        """Filter a location by a list of properties. NOTE you can also do this directly in RISE. Make sure you actually need this and can't fetch up front."""
        list_of_properties: list[str] = (
            [select_properties]
            if isinstance(select_properties, str)
            else select_properties
        )

        locationsToParams = self.get_parameters(cache)
        for param in list_of_properties:
            for location, paramList in locationsToParams.items():
                if param not in paramList:
                    response = self.drop_location(int(location))

        return response
    
    def filter_by_bbox(
        self,
        bbox: Optional[list] = None,
        z: Optional[str] = None,
    ) :
        if bbox:
            parse_result = parse_bbox(bbox)
            shapely_box = parse_result[0] if parse_result else None
            z = parse_result[1] if parse_result else z

        shapely_box = parse_bbox(bbox)[0] if bbox else None
        # TODO what happens if they specify both a bbox with z and a z value?
        z = parse_bbox(bbox)[1] if bbox else z

        return self._filter_by_geometry(shapely_box, z)