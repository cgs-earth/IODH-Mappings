# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Optional
from rise.lib.cache import RISECache
from rise.lib.helpers import flatten_values, getResultUrlFromCatalogUrl, safe_run_async
from rise.lib.location import LocationResponse, LocationResponseWithIncluded
from rise.lib.types.catalogItem import CatalogItemResponse

LOGGER = logging.getLogger(__name__)


class LocationResultBuilder:
    def __init__(self, cache: RISECache, base_response: LocationResponseWithIncluded):
        self.cache = cache
        self.base_response = base_response

    def fetch_results(self, time_filter: Optional[str] = None):
        """Given a location that contains just catalog item ids, fill in the catalog items with the full
        endpoint response for the given catalog item so it can be more easily used for complex joins
        """

        # Make a dictionary from an existing response, no fetch needed
        locationToCatalogItemUrls = self.base_response.get_catalogItemURLs()

        catalogItemUrls = flatten_values(locationToCatalogItemUrls)

        catalogItemUrlToResponse = safe_run_async(
            self.cache.get_or_fetch_group(catalogItemUrls)
        )

        # Fetch all results in parallel before looping through each location to add them in the json
        resultUrls = [
            getResultUrlFromCatalogUrl(url, time_filter) for url in catalogItemUrls
        ]
        assert len(resultUrls) == len(
            set(resultUrls)
        ), "Duplicate result urls when adding results to the catalog items"

        LOGGER.debug(f"Fetching {resultUrls}; {len(resultUrls)} in total")
        timeseriesResults = safe_run_async(self.cache.get_or_fetch_group(resultUrls))

        for i, location in enumerate(self.base_response.data):
            catalogItemUrls = locationToCatalogItemUrls.get(location.id)
            if not catalogItemUrls:
                continue

            for j, catalogItem in enumerate(catalogItemUrls):
                fetchedLocation = catalogItemUrlToResponse[catalogItem]
                model = CatalogItemResponse.model_validate(fetchedLocation)
                fetchedData = model.data

                if not model.data[i].relationships.catalogItems:
                    model.data[i].relationships.catalogItems = {"data": []}

                model.data[i].relationships.catalogItems.data.append(fetchedData)

                base_catalog_item_j = model.data[i].relationships.catalogItems.data[j]
                associated_res_url = getResultUrlFromCatalogUrl(
                    catalogItem, time_filter
                )
                if not associated_res_url:
                    results_for_catalog_item_j = None
                else:
                    results_for_catalog_item_j = timeseriesResults[associated_res_url].get(
                        "data", None
                    )
                    base_catalog_item_j["results"] = results_for_catalog_item_j

        return model
