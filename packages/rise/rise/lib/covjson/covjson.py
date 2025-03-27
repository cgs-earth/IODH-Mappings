# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from datetime import datetime
import logging
from typing import Any, Tuple, cast

from com.helpers import EDRFieldsMapping, await_

from covjson_pydantic.coverage import Coverage, CoverageCollection
from covjson_pydantic.parameter import Parameter
from covjson_pydantic.unit import Unit
from covjson_pydantic.observed_property import ObservedProperty
from rise.lib.cache import RISECache
from rise.lib.add_results import DataNeededForCovjson, ParameterWithResults
from covjson_pydantic.domain import Domain, Axes, ValuesAxis, DomainType
from rise.lib.covjson.types import CoverageCollectionDict
from covjson_pydantic.ndarray import NdArrayFloat
from covjson_pydantic.reference_system import (
    ReferenceSystemConnectionObject,
    ReferenceSystem,
)

LOGGER = logging.getLogger(__name__)


class CovJSONBuilder:
    """A helper class for building CovJSON from a Rise JSON Response"""

    def __init__(self, cache: RISECache):
        self._cache = cache

    def _generate_coverage_item(
        self,
        location_type: str,
        coords: list[Any] | Tuple[float, float],
        times: list[datetime],
        naturalLanguageName: str,
        param: ParameterWithResults,
    ) -> Coverage:
        # if it is a point it will have different geometry
        isPoint = location_type == "Point"
        if isPoint:
            x, y = coords[0], coords[1]

        cov = Coverage(
            type="Coverage",
            domain=Domain(
                type="Domain",
                domainType=DomainType.point_series if isPoint else "PolygonSeries",  # type: ignore
                axes=Axes(
                    t=ValuesAxis(values=times),
                    x=ValuesAxis(values=[x]),  # type: ignore Pyright says it is possibly unbound but this isn't possible since if it is a point it will have coords
                    y=ValuesAxis(values=[y]),  # type: ignore
                )
                if isPoint
                else Axes(
                    composite=ValuesAxis(
                        values=[tuple(coords)], dataType=location_type
                    ),
                    t=ValuesAxis(values=times),
                ),
                referencing=[
                    ReferenceSystemConnectionObject(
                        coordinates=["x", "y"],
                        system=ReferenceSystem(
                            type="GeographicCRS",
                            id="http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                        ),
                    ),
                    ReferenceSystemConnectionObject(
                        coordinates=["t"],
                        system=ReferenceSystem(
                            type="TemporalRS",
                            id="http://www.opengis.net/def/crs/OGC/1.3/CRS84",
                        ),
                    ),
                ],
            ),
            ranges={
                naturalLanguageName: NdArrayFloat(
                    shape=[len(param.timeseriesResults)],
                    values=param.timeseriesResults,
                    axisNames=["t"],
                    dataType="float",
                    type="NdArray",
                )
            },
        )
        return cov

    def _get_parameters(
        self,
        paramsToGeoJsonOutput: EDRFieldsMapping,
        location_response: list[DataNeededForCovjson],
    ) -> dict[str, Parameter]:
        relevant_parameters = []
        for location in location_response:
            for p in location.parameters:
                relevant_parameters.append(p.parameterId)

        params = {}
        for param_id in relevant_parameters:
            if param_id not in paramsToGeoJsonOutput:
                LOGGER.error(
                    f"Could not find metadata for {param_id} in {sorted(paramsToGeoJsonOutput.keys())}"
                )
                continue

            associatedData = paramsToGeoJsonOutput[param_id]

            naturalLanguageName = associatedData["title"]

            params[naturalLanguageName] = Parameter(
                type="Parameter",
                id=param_id,
                unit=Unit(symbol=associatedData["x-ogc-unit"]),
                observedProperty=ObservedProperty(
                    label={"en": associatedData["title"]},
                    id=param_id,
                    description={"en": associatedData["description"]},
                ),
            )

        return params

    def _get_coverages(
        self,
        locationsWithResults: list[DataNeededForCovjson],
        paramsToGeoJsonOutput,
    ) -> list[Coverage]:
        """Return the data needed for the 'coverage' key in the covjson response"""

        coverages = []
        for location_feature in locationsWithResults:
            for param in location_feature.parameters:
                if not (  # ensure param contains data so it can be used for covjson
                    param.timeseriesResults
                ):
                    # Since coveragejson does not allow a parameter without results,
                    # we can skip adding the parameter/location combination all together
                    continue

                naturalLanguageName = paramsToGeoJsonOutput[str(param.parameterId)][
                    "title"
                ]

                datesAsDatetimeObjs = [
                    datetime.fromisoformat(d) for d in param.timeseriesDates if d
                ]
                coverage_item = self._generate_coverage_item(
                    location_feature.locationType,
                    location_feature.geometry,
                    datesAsDatetimeObjs,
                    naturalLanguageName,
                    param,
                )

                coverages.append(coverage_item)

        return coverages

    def render(
        self, location_response: list[DataNeededForCovjson]
    ) -> CoverageCollectionDict:
        paramIdToMetadata: EDRFieldsMapping = await_(
            self._cache.get_or_fetch_parameters()
        )
        coverages = self._get_coverages(location_response, paramIdToMetadata)
        parameters = self._get_parameters(
            paramIdToMetadata, location_response=location_response
        )

        # we have to cast since pydantic model dump returns a generic dict
        # but we want to narrow it based on our known schema
        return cast(
            CoverageCollectionDict,
            CoverageCollection(
                coverages=coverages,
                domainType=DomainType.point_series,
                parameters=parameters,
            ).model_dump(by_alias=True, exclude_none=True),
        )
