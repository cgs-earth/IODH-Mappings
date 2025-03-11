# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Any, Literal, Optional, Tuple

from pydantic import BaseModel

from rise.lib.cache import RISECache
from rise.lib.helpers import flatten_values, getResultUrlFromCatalogUrl, safe_run_async
from rise.lib.location import LocationResponseWithIncluded
from rise.lib.types.results import ResultResponse

LOGGER = logging.getLogger(__name__)


class ParameterWithResults(BaseModel):
    catalogItemId: str
    parameterId: str
    timeseriesResults: list
    timeseriesDates: list[str]


class DataNeededForCovjson(BaseModel):
    """
    This class represents the smallest amount of data needed for making covjson
    from rise. We pass around a small class in an effort to make the ETL cleaner and simpler
    """
    location: str
    locationType: Literal["Point", "Polygon", "LineString"]
    geometry: list[Any] | Tuple[float, float]
    parameters: list[ParameterWithResults]


class LocationResultBuilder:
    """
    Helper class for associating a location/ response from RISE
    with its associated timeseries data results
    """

    def __init__(self, cache: RISECache, base_response: LocationResponseWithIncluded):
        self.cache = cache
        self.base_response = base_response
        self.locationToCatalogItemUrls = self.base_response.get_catalogItemURLs()
        self.catalogItemToLocationId = {}
        for location, catalogItems in self.locationToCatalogItemUrls.items():
            for catalogItem in catalogItems:
                self.catalogItemToLocationId[catalogItem] = location

    def _get_all_timeseries_data(self, time_filter: Optional[str] = None):
        # Make a dictionary from an existing response
        catalogItemUrls = flatten_values(self.locationToCatalogItemUrls)
        resultUrls = [
            getResultUrlFromCatalogUrl(url, time_filter) for url in catalogItemUrls
        ]
        assert len(resultUrls) == len(
            set(resultUrls)
        ), "Duplicate result urls when adding results to the catalog items"
        LOGGER.debug(f"Fetching {resultUrls}; {len(resultUrls)} in total")
        return safe_run_async(self.cache.get_or_fetch_group(resultUrls))

    def _get_timeseries_for_catalogitem(self, catalogItem):
        if catalogItem not in self.timeseriesResults:
            return None
        return self.timeseriesResults[catalogItem]

    def load_results(
        self, time_filter: Optional[str] = None
    ) -> list[DataNeededForCovjson]:
        """Given a location that contains just catalog item ids, fill in the catalog items with the full
        endpoint response for the given catalog item so it can be more easily used for complex joins
        """

        self.timeseriesResults = self._get_all_timeseries_data(time_filter)

        locations_with_data: list[DataNeededForCovjson] = []

        for location in self.base_response.data:
            paramAndResults: list[ParameterWithResults] = []
            for catalogItemUrl in self.locationToCatalogItemUrls[location.id]:
                catalogUrlAsResultUrl = getResultUrlFromCatalogUrl(
                    catalogItemUrl, time_filter
                )
                timseriesResults = self.timeseriesResults[catalogUrlAsResultUrl]
                timeseriesModel = ResultResponse.model_validate(timseriesResults)
                paramAndResults.append(
                    ParameterWithResults(
                        catalogItemId=catalogItemUrl,
                        timeseriesResults=timeseriesModel.get_results(),
                        timeseriesDates=timeseriesModel.get_dates(),
                        parameterId=timeseriesModel.get_parameter_id(),
                    )
                )
            locations_with_data.append(
                DataNeededForCovjson(
                    locationType=location.attributes.locationCoordinates.type,
                    location=location.id,
                    parameters=paramAndResults,
                    geometry=location.attributes.locationCoordinates.coordinates,
                )
            )

        return locations_with_data
