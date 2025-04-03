from awdb_com.locations import LocationCollection
from awdb_com.types import StationDTO
from awdb_forecasts.lib.covjson_builder import CovjsonBuilder
from com.cache import RedisCache
from com.helpers import EDRFieldsMapping, await_
from rise.lib.covjson.types import CoverageCollectionDict
from typing import Optional, cast


type longitudeAndLatitude = tuple[float, float]


class ForecastLocationCollection(LocationCollection):
    def __init__(
        self,
        select_properties: Optional[list[str]] = None,
        only_stations_with_forecasts=True,
    ):
        self.cache = RedisCache()
        # snotel also proxies usgs so we just want to get SNOTEL stations
        url = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?returnForecastPointMetadata=true&returnReservoirMetadata=false&returnStationElements=false&activeOnly=true"
        if select_properties:
            url += f"&elements={','.join(select_properties)}"
        result = await_(self.cache.get_or_fetch(url))
        self.locations = [
            StationDTO.model_validate(res) for res in result if res.get("forecastPoint")
        ]

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
