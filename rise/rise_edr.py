# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Any, ClassVar, Optional

from pygeoapi.provider.base import (
    ProviderQueryError,
)
from pygeoapi.provider.base_edr import BaseEDRProvider
from rise.lib.covjson.covjson import CovJSONBuilder
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.cache import RISECache
from rise.lib.helpers import safe_run_async
from rise.lib.add_results import LocationResultBuilder

LOGGER = logging.getLogger(__name__)


class RiseEDRProvider(BaseEDRProvider):
    """The EDR Provider for the USBR Rise API"""

    LOCATION_API: ClassVar[str] = "https://data.usbr.gov/rise/api/location"
    BASE_API: ClassVar[str] = "https://data.usbr.gov"
    cache: RISECache

    def __init__(self, provider_def: dict[str, Any]):
        """
        Initialize object

        :param provider_def: provider definition

        :returns: rise.base_edr.RiseEDRProvider
        """
        try:
            self.cache = RISECache(provider_def["cache"])
        except KeyError:
            LOGGER.error(
                "You must specify a cache implementation in the config.yml for RISE"
            )
            raise

        provider_def = {
            "name": "Rise EDR",
            "type": "feature",
            "data": "remote",
        }

        super().__init__(provider_def)

        self.instances = []

    def get_or_fetch_all_param_filtered_pages(
        self, properties_to_filter_by: Optional[list[str]] = None
    ):
        """Return all locations which contain"""
        # RISE has an API for fetching locations by property/param ids. Thus, we want to fetch only relevant properties if we have them
        if properties_to_filter_by:
            base_url = "https://data.usbr.gov/rise/api/location?&"
            for prop in properties_to_filter_by:
                assert isinstance(prop, str)
                base_url += f"parameterId%5B%5D={prop}&"
            base_url = base_url.removesuffix("&")
        else:
            base_url = "https://data.usbr.gov/rise/api/location?"
        base_url += "&include=catalogRecords.catalogItems"
        return self.cache.get_or_fetch_all_pages(base_url)

    @BaseEDRProvider.register()
    def locations(
        self,
        location_id: Optional[int] = None,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
        crs: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract data from location
        """
        if not location_id and datetime_:
            raise ProviderQueryError("Can't filter by date on every location")

        if location_id:
            url: str = f"https://data.usbr.gov/rise/api/location/{location_id}?include=catalogRecords.catalogItems"
            raw_resp = safe_run_async(self.cache.get_or_fetch(url))
            response = LocationResponseWithIncluded(**raw_resp)
        else:
            raw_resp = self.get_or_fetch_all_param_filtered_pages(select_properties)
            response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        # If a location exists but has no CatalogItems, it should not appear in locations
        response = response.drop_locations_without_catalogitems()

        # FROM SPEC: If a location id is not defined the API SHALL return a GeoJSON features array of valid location identifiers,
        if not any([crs, datetime_, location_id]) or format_ == "geojson":
            return response.to_geojson()

        # if we are returning covjson we need to fetch the results and fill in the json
        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(response_with_results)

    def get_fields(self):
        """Get the list of all parameters (i.e. fields) that the user can filter by"""
        if self._fields:
            return self._fields

        self._fields = self.cache.get_or_fetch_parameters()

        return self._fields

    @BaseEDRProvider.register()
    def cube(
        self,
        bbox: list,
        datetime_: Optional[str] = None,
        select_properties: Optional[list] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Returns a data cube defined by bbox and z parameters

        :param bbox: `list` of minx,miny,maxx,maxy coordinate values as `float`
        :param datetime_: temporal (datestamp or extent)
        :param z: vertical level(s)
        :param format_: data format of output
        """

        raw_resp = self.get_or_fetch_all_param_filtered_pages(select_properties)
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        if datetime_:
            response = response.drop_outside_of_date_range(datetime_)

        response = response.drop_outside_of_bbox(bbox, z)

        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(response_with_results)

    @BaseEDRProvider.register()
    def area(
        self,
        # Well known text (WKT) representation of the geometry for the area
        wkt: str,
        select_properties: list[str] = [],
        datetime_: Optional[str] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract and return coverage data from a specified area.
        Example: http://localhost:5000/collections/rise-edr/area?coords=POLYGON%20((-109.204102%2047.010226,%20-104.655762%2047.010226,%20-104.655762%2049.267805,%20-109.204102%2049.267805,%20-109.204102%2047.010226))&f=json
        """

        raw_resp = self.get_or_fetch_all_param_filtered_pages(select_properties)
        response = LocationResponseWithIncluded.from_api_pages(raw_resp)

        if datetime_:
            response = response.drop_outside_of_date_range(datetime_)

        if wkt != "":
            response = response.drop_outside_of_wkt(wkt, z)

        builder = LocationResultBuilder(cache=self.cache, base_response=response)
        response_with_results = builder.load_results(time_filter=datetime_)
        return CovJSONBuilder(self.cache).fill_template(response_with_results)

    @BaseEDRProvider.register()
    def items(self, **kwargs):
        # We have to define this since pygeoapi has a limitation and needs both EDR and OAF for items
        # https://github.com/geopython/pygeoapi/issues/1748
        pass

    def __repr__(self):
        return "<RiseEDRProvider>"
