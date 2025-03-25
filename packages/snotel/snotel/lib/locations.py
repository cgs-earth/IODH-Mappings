# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from com.cache import RedisCache
from com.env import TRACER
from com.geojson.types import (
    GeojsonFeatureDict,
    GeojsonFeatureCollectionDict,
    SortDict,
    sort_by_properties_in_place,
)
from com.helpers import (
    EDRField,
    OAFFieldsMapping,
    await_,
    parse_bbox,
    parse_date,
    parse_z,
)
import geojson_pydantic
from rise.lib.types.helpers import ZType
from snotel.lib.result import ResultCollection
from snotel.lib.types import StationDTO
import shapely
from typing import List, Optional, assert_never
from covjson_pydantic.coverage import Coverage, CoverageCollection
from covjson_pydantic.parameter import Parameter
from covjson_pydantic.unit import Unit
from covjson_pydantic.observed_property import ObservedProperty
from covjson_pydantic.domain import Domain, Axes, ValuesAxis, DomainType
from covjson_pydantic.ndarray import NdArrayFloat
from covjson_pydantic.reference_system import (
    ReferenceSystemConnectionObject,
    ReferenceSystem,
)


class LocationCollection:
    """A wrapper class containing locations and methods to filter them"""

    locations: list[StationDTO]

    def __init__(self):
        self.cache = RedisCache()
        # snotel also proxies usgs so we just want to get SNOTEL stations
        JUST_SNOTEL_STATIONS = "*:*:SNTL"
        result = await_(
            self.cache.get_or_fetch(
                f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&stationTriplets={JUST_SNOTEL_STATIONS}"
            )
        )
        self.locations = [StationDTO.model_validate(res) for res in result]

    def drop_all_locations_but_id(self, location_id: str):
        data = [v for v in self.locations if v.stationId == str(location_id)]
        self.locations = data
        return self

    def drop_after_limit(self, limit: int):
        """
        Return only the location data for the locations in the list up to the limit
        """
        self.locations = self.locations[:limit]
        return self

    def drop_before_offset(self, offset: int):
        """
        Return only the location data for the locations in the list after the offset
        """
        self.locations = self.locations[offset:]
        return self

    def drop_all_locations_outside_bounding_box(self, bbox):
        geometry, z = parse_bbox(bbox)
        return self._filter_by_geometry(geometry, z)

    def select_date_range(self, datetime_: str):
        """
        Drop locations if their begin-end range is outside of the query date range
        """
        location_indices_to_remove = set()

        parsed_date: list[datetime] = parse_date(datetime_)
        MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE = "2100-01-01"

        if len(parsed_date) == 2:
            startQuery, endQuery = parsed_date

            for i, location in enumerate(self.locations):
                if not location.beginDate or not location.endDate:
                    location_indices_to_remove.add(i)
                    continue
                skipEndDateCheck = location.endDate.startswith(
                    MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE
                )
                startDate = datetime.fromisoformat(location.beginDate)
                endDate = datetime.fromisoformat(location.endDate)

                locationIsInsideQueryRange = startDate <= startQuery and (
                    endQuery <= endDate if not skipEndDateCheck else True
                )
                if not locationIsInsideQueryRange:
                    location_indices_to_remove.add(i)

        elif len(parsed_date) == 1:
            for i, location in enumerate(self.locations):
                if not location.beginDate or not location.endDate:
                    location_indices_to_remove.add(i)
                    continue
                skipEndDateCheck = (
                    location.endDate == MAGIC_UPSTREAM_DATE_SIGNIFYING_STILL_IN_SERVICE
                )
                startDate = datetime.fromisoformat(location.beginDate)
                endDate = datetime.fromisoformat(location.endDate)
                if parsed_date[0] < startDate or (
                    not skipEndDateCheck and parsed_date[0] > endDate
                ):
                    location_indices_to_remove.add(i)

        else:
            raise RuntimeError(
                "datetime_ must be a date or date range with two dates separated by '/' but got {}".format(
                    datetime_
                )
            )

        # delete them backwards so we don't have to make a copy of the list or mess up indices while iterating
        for index in sorted(location_indices_to_remove, reverse=True):
            del self.locations[index]

        return self

    def to_geojson(
        self,
        itemsIDSingleFeature=False,
        skip_geometry: Optional[bool] = False,
        select_properties: Optional[list[str]] = None,
        properties: Optional[list[tuple[str, str]]] = None,
        fields_mapping: dict[str, EDRField] | OAFFieldsMapping = {},
        sortby: Optional[list[SortDict]] = None,
    ) -> GeojsonFeatureCollectionDict | GeojsonFeatureDict:
        """
        Return a geojson feature if the client queried for items/{itemId} or a feature collection if they queried for items/ even if the result is only one item
        """
        features: list[geojson_pydantic.Feature] = []

        for loc in self.locations:
            feature: GeojsonFeatureDict = {
                "type": "Feature",
                "properties": loc.model_dump(exclude={"latitude", "longitude"}),
                "geometry": {
                    "type": "Point",
                    "coordinates": [loc.longitude, loc.latitude],
                }
                if not skip_geometry
                else None,
                "id": loc.stationId,
            }
            if select_properties:
                feature["properties"] = {
                    k: v
                    for k, v in feature["properties"].items()
                    if k in select_properties
                }
            features.append(geojson_pydantic.Feature.model_validate(feature))

        if sortby:
            sort_by_properties_in_place(features, sortby)

        geojson_pydantic.FeatureCollection(
            type="FeatureCollection",
            features=features,
        )
        if itemsIDSingleFeature:
            assert len(features) == 1, (
                "The user queried a single item but we have more than one present. This is a sign that filtering by locationid wasn't done properly"
            )
            return GeojsonFeatureDict(**features[0].model_dump())
        return GeojsonFeatureCollectionDict(
            **{
                "type": "FeatureCollection",
                "features": [feature.model_dump(by_alias=True) for feature in features],
            }
        )

    @TRACER.start_as_current_span("geometry_filter")
    def _filter_by_geometry(
        self,
        geometry: Optional[shapely.geometry.base.BaseGeometry],
        # Vertical level
        z: Optional[str] = None,
    ):
        """
        Filter a list of locations by any arbitrary geometry; if they are not inside of it, drop their data
        """
        indices_to_pop = set()
        parsed_z = parse_z(str(z)) if z else None

        for i, v in enumerate(self.locations):
            elevation = v.elevation

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
                if v.latitude is None or v.longitude is None:
                    indices_to_pop.add(i)
                    continue

                locationPoint = shapely.geometry.point.Point(
                    # need to convert the pydantic model to a simple
                    # dict to use shapely with it
                    [v.longitude, v.latitude]
                )

                if not geometry.contains(locationPoint):
                    indices_to_pop.add(i)

        # by reversing the list we pop from the end so the
        # indices will be in the correct even after removing items
        for i in sorted(indices_to_pop, reverse=True):
            self.locations.pop(i)

        return self

    def to_covjson(self):
        stationTriples: list[str] = [
            location.stationTriplet
            for location in self.locations
            if location.stationTriplet
        ]
        triplesToData = ResultCollection().fetch_all_data(
            station_triplets=stationTriples
        )

        coverages: list[Coverage] = []

        parameters: dict[str, Parameter] = {}

        for triple, result in triplesToData.items():
            assert result.data
            for datastream in result.data:
                assert datastream.stationElement
                assert datastream.stationElement.elementCode
                param = Parameter(
                    type="Parameter",
                    unit=Unit(symbol=datastream.stationElement.storedUnitCode),
                    id=datastream.stationElement.elementCode,
                    observedProperty=ObservedProperty(
                        label={"en": datastream.stationElement.elementCode},
                        id=triple,
                    ),
                )
                parameters[datastream.stationElement.elementCode] = param

                assert datastream.values
                values: List[float] = [
                    data.value for data in datastream.values if data.value and data.date
                ]
                times = [
                    datetime.fromisoformat(data.date).replace(tzinfo=timezone.utc)
                    for data in datastream.values
                    if data.date and data.value
                ]
                assert len(values) == len(times)
                cov = Coverage(
                    type="Coverage",
                    domain=Domain(
                        type="Domain",
                        domainType=DomainType.point_series,
                        axes=Axes(
                            t=ValuesAxis(values=times),
                            x=ValuesAxis(values=[0]),
                            y=ValuesAxis(values=[0]),
                        ),
                        referencing=[
                            ReferenceSystemConnectionObject(
                                coordinates=["x", "y"],
                                system=ReferenceSystem(
                                    type="GeographicCRS",
                                    id="http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                                ),
                            )
                        ],
                    ),
                    ranges={
                        datastream.stationElement.elementCode: NdArrayFloat(
                            shape=[len(values)],
                            values=values,  # type: ignore
                            axisNames=["t"],
                        ),
                    },
                )
                coverages.append(cov)

        covCol = CoverageCollection(coverages=coverages, parameters=parameters)
        return covCol.model_dump(by_alias=True, exclude_none=True)
