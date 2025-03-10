# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Optional
from rise.lib.cache import RISECache
from rise.lib.helpers import flatten_values, getResultUrlFromCatalogUrl, safe_run_async
from rise.lib.location import LocationResponseWithIncluded

LOGGER = logging.getLogger(__name__)


class LocationResultBuilder:
    """
    Helper class for associating a location/ response from RISE
    with its associated timeseries data results
    """

    def __init__(self, cache: RISECache, base_response: LocationResponseWithIncluded):
        self.cache = cache
        self.base_response = base_response

    def _get_all_timeseries_data(
        self, locationToCatalogItemUrls, time_filter: Optional[str] = None
    ):
        # Make a dictionary from an existing response
        catalogItemUrls = flatten_values(locationToCatalogItemUrls)
        resultUrls = [
            getResultUrlFromCatalogUrl(url, time_filter) for url in catalogItemUrls
        ]
        assert len(resultUrls) == len(
            set(resultUrls)
        ), "Duplicate result urls when adding results to the catalog items"
        LOGGER.debug(f"Fetching {resultUrls}; {len(resultUrls)} in total")
        timeseriesResults = safe_run_async(self.cache.get_or_fetch_group(resultUrls))
        return timeseriesResults

    def fetch_results(self, time_filter: Optional[str] = None):
        """Given a location that contains just catalog item ids, fill in the catalog items with the full
        endpoint response for the given catalog item so it can be more easily used for complex joins
        """

        locationToCatalogItemUrls = self.base_response.get_catalogItemURLs()
        resultUrlToCatalogItem = {
            getResultUrlFromCatalogUrl(url, time_filter): url
            for url in flatten_values(locationToCatalogItemUrls)
        }

        resultUrlToTimeseries = self._get_all_timeseries_data(
            locationToCatalogItemUrls, time_filter
        )

        for i, location in enumerate(self.base_response.data):
            catalogItemUrls = locationToCatalogItemUrls.get(location.id)
            if not catalogItemUrls:
                # if a location didn't have any catalogitems, it also can't
                # have any timeseries data and thus should be skipped
                continue

            for j, catalogItem in enumerate(catalogItemUrls):
                self.base_response.included[
                    i
                ].relationships.catalogItems = timeseriesResults[j]

        return self.base_response
