# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Literal, Optional

from com.helpers import get_oaf_fields_from_pydantic_model
from pygeoapi.provider.base import BaseProvider
from pygeoapi.util import crs_transform
from com.geojson.types import GeojsonFeature, GeojsonFeatureCollectionDict
from rise.lib.types.sorting import SortDict
from com.cache import RedisCache
from snotel.lib.locations import LocationCollection
from snotel.lib.types import StationDTO

LOGGER = logging.getLogger(__name__)


class SnotelProvider(BaseProvider):
    """Rise Provider for OGC API Features"""

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition
        """
        super().__init__(provider_def)
        self.cache = RedisCache()
        self.get_fields()

    def items(
        self,
        bbox: list = [],
        datetime_: Optional[str] = None,
        resulttype: Optional[Literal["hits", "results"]] = "results",
        # select only features that contains all the `select_properties` values
        select_properties: Optional[
            list[str]
        ] = None,  # query this with ?properties in the actual url
        # select only features that contains all the `properties` with their corresponding values
        properties: list[tuple[str, str]] = [],
        sortby: Optional[list[SortDict]] = None,
        limit: Optional[int] = None,
        itemId: Optional[
            str
        ] = None,  # unlike edr, this is a string; we need to case to an int before filtering
        offset: Optional[int] = 0,
        skip_geometry: Optional[bool] = False,
        **kwargs,
    ) -> GeojsonFeatureCollectionDict | GeojsonFeature:
        collection = LocationCollection()
        if itemId:
            collection = collection.drop_all_locations_but_id(itemId)
        if bbox:
            collection = collection.drop_all_locations_outside_bounding_box(bbox)

        if limit:
            collection = collection.drop_after_limit(limit)
        if offset:
            collection = collection.drop_before_offset(offset)

        if resulttype == "hits":
            return {
                "type": "FeatureCollection",
                "features": [],
                "numberMatched": len(collection.locations),
            }

        return collection.to_geojson(skip_geometry, itemId is not None)

    @crs_transform
    def query(self, **kwargs):
        return self.items(**kwargs)

    def get(self, identifier, **kwargs):
        """
        query CSV id

        :param identifier: feature id

        :returns: dict of single GeoJSON feature
        """

        return self.items(itemId=identifier, bbox=[], **kwargs)

    def get_fields(self, **kwargs):
        """
        Get provider field information (names, types)

        Example response: {'field1': 'string', 'field2': 'number'}

        :returns: dict of field names and their associated JSON Schema types
        """
        if not self._fields:
            self._fields = get_oaf_fields_from_pydantic_model(StationDTO)
        return self._fields
