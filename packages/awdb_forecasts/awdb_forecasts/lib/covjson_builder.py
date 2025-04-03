# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from datetime import datetime, timezone
from typing import Optional
from awdb_forecasts.lib.forecasts import ForecastResultCollection
from com.helpers import EDRFieldsMapping
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
from awdb_com.types import ForecastDataDTO


class CovjsonBuilder:
    """
    A helper class for constructing a coveragejson response for EDR queries
    """

    coverages: list[Coverage]
    parameters: dict[str, Parameter] = {}
    triplesToData: dict[str, list[ForecastDataDTO]]

    def __init__(
        self,
        station_triples: list[str],
        triplesToGeometry: dict[str, tuple[float, float]],
        fieldsMapper: EDRFieldsMapping,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
    ):
        """Initialize the builder object and fetch the necessary timeseries data"""
        self.triplesToData = ForecastResultCollection().fetch_all_data(
            station_triples, datetime_filter=datetime_
        )
        self.triplesToGeometry = triplesToGeometry
        self.fieldsMapper = fieldsMapper
        self.select_properties = select_properties

    def _generate_parameter(self, id: str, datastream: ForecastDataDTO):
        """Given a triple and an associated datastream, generate a covjson parameter that describes its properties and unit"""
        assert datastream.elementCode
        edr_field = self.fieldsMapper[datastream.elementCode]
        param = Parameter(
            type="Parameter",
            unit=Unit(symbol=datastream.unitCode),
            id=edr_field["title"],
            observedProperty=ObservedProperty(
                label={"en": datastream.elementCode},
                id=edr_field["title"],
                description={"en": edr_field["description"]},
            ),
        )
        return param

    def _generate_coverage(self, triple: str, datastream: ForecastDataDTO):
        """Given a datastream generate a covjson coverage for the timeseries data"""

        assert datastream.forecastValues
        values: list[float] = [
            # value for prob, value in datastream.forecastValues.items()
            1
        ]
        assert datastream.publicationDate
        times = [
            datetime.fromisoformat(datastream.publicationDate).replace(
                tzinfo=timezone.utc
            )
        ]
        assert len(values) == len(times)
        longitude, latitude = self.triplesToGeometry[triple]
        assert datastream.elementCode
        cov = Coverage(
            type="Coverage",
            domain=Domain(
                type="Domain",
                domainType=DomainType.point_series,
                axes=Axes(
                    t=ValuesAxis(values=times),
                    x=ValuesAxis(values=[longitude]),
                    y=ValuesAxis(values=[latitude]),
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
                self.fieldsMapper[datastream.elementCode]["title"]: NdArrayFloat(
                    shape=[len(values)],
                    values=values,  # type: ignore
                    axisNames=["t"],
                ),
            },
        )
        return cov

    def render(self):
        """Build the covjson and return it as a dictionary"""
        coverages: list[Coverage] = []
        parameters: dict[str, Parameter] = {}

        for triple, result in self.triplesToData.items():
            assert result
            for datastream in result:
                assert datastream.elementCode
                title = self.fieldsMapper[datastream.elementCode]["title"]
                id = datastream.elementCode
                parameters[title] = self._generate_parameter(triple, datastream)
                if self.select_properties and id not in self.select_properties:
                    continue
                cov = self._generate_coverage(triple, datastream)
                coverages.append(cov)

                assert len(cov.ranges) == 1

        covCol = CoverageCollection(
            coverages=coverages,
            domainType=DomainType.point_series,
            parameters=parameters,
        )
        return covCol.model_dump(
            by_alias=True, exclude_none=True
        )  # pydantic covjson must dump with exclude none
