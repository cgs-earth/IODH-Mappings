# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

# generated by datamodel-codegen:
#   filename:  https://wcc.sc.egov.usda.gov/awdbRestApi/v3/api-docs
#   timestamp: 2025-04-03T18:25:13+00:00

from __future__ import annotations

from enum import Enum
from typing import Annotated, Dict, List, Optional

from msgspec import Meta, Struct


class DataValueDTO(Struct):
    date: Optional[
        Annotated[
            str,
            Meta(
                description="The timestamp of the data. Used only for DAILY and HOURLY durations."
            ),
        ]
    ] = None
    month: Optional[
        Annotated[
            int,
            Meta(
                description="The month of the data value (1-12). Used only for MONTHLY and SEMIMONTHLY durations."
            ),
        ]
    ] = None
    monthPart: Optional[
        Annotated[
            str,
            Meta(
                description="The half of month of the data value ('1' for first half, '2' for second half). Used only for SEMIMONTHLY durations."
            ),
        ]
    ] = None
    year: Optional[
        Annotated[
            int,
            Meta(
                description="The year of the data value. Used only for WATER_YEAR, CALENDAR_YEAR, MONTHLY, and SEMIMONTHLY durations."
            ),
        ]
    ] = None
    collectionDate: Optional[
        Annotated[
            str,
            Meta(
                description="The date the data value was collected. Used only for SEMIMONTHLY durations."
            ),
        ]
    ] = None
    value: Optional[Annotated[float, Meta(description="The data value")]] = None
    qcFlag: Optional[
        Annotated[str, Meta(description="The qc flag of the data value")]
    ] = None
    qaFlag: Optional[
        Annotated[str, Meta(description="The qa flag of the data value")]
    ] = None
    origValue: Optional[
        Annotated[float, Meta(description="The original data value")]
    ] = None
    origQcFlag: Optional[
        Annotated[str, Meta(description="The original qc flag of the data value")]
    ] = None
    average: Optional[Annotated[float, Meta(description="The 30-year average")]] = None
    median: Optional[Annotated[float, Meta(description="The 30-year median")]] = None


class DcoDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The DCO code")]] = None
    name: Optional[Annotated[str, Meta(description="The DCO Name")]] = None


class DurationDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The duration code")]] = None
    name: Optional[Annotated[str, Meta(description="The duration name")]] = None
    durationMinutes: Optional[
        Annotated[str, Meta(description="The duration in minutes")]
    ] = None


class ElementDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The element code")]] = None
    name: Optional[Annotated[str, Meta(description="The element name")]] = None
    physicalElementName: Optional[
        Annotated[str, Meta(description="The physical element name")]
    ] = None
    functionCode: Optional[Annotated[str, Meta(description="The function code")]] = None
    dataPrecision: Optional[
        Annotated[int, Meta(description="The precision of the data")]
    ] = None
    description: Optional[
        Annotated[str, Meta(description="The element description")]
    ] = None
    storedUnitCode: Optional[
        Annotated[str, Meta(description="The stored unit code")]
    ] = None
    englishUnitCode: Optional[
        Annotated[str, Meta(description="The english unit code")]
    ] = None
    metricUnitCode: Optional[
        Annotated[str, Meta(description="The metric unit code")]
    ] = None


class ForecastDataDTO(Struct):
    elementCode: Optional[
        Annotated[
            str, Meta(description="The element code related to the forecast record.")
        ]
    ] = None
    forecastPeriod: Optional[
        Annotated[
            List[str],
            Meta(
                description="The start (MM-DD) and end (MM-DD) of the forecast period that the forecast is for."
            ),
        ]
    ] = None
    forecastStatus: Optional[
        Annotated[str, Meta(description="Indicates the status of the Forecast.")]
    ] = None
    issueDate: Optional[
        Annotated[str, Meta(description="The issue date of the forecast.")]
    ] = None
    periodNormal: Optional[
        Annotated[float, Meta(description="The forecast period normal.")]
    ] = None
    publicationDate: Optional[
        Annotated[str, Meta(description="The publication date of the forecast value.")]
    ] = None
    unitCode: Optional[
        Annotated[str, Meta(description="The unit code of a forecast.")]
    ] = None
    forecastValues: Optional[
        Annotated[
            Dict[str, float],
            Meta(
                description="A dictionary of forecast values where the key is the exceedence probability and the value is the corresponding forecast value."
            ),
        ]
    ] = None


class ForecastPeriodDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The forecast period code")]] = None
    name: Optional[Annotated[str, Meta(description="The forecast period name")]] = None
    description: Optional[
        Annotated[str, Meta(description="The forecast period description")]
    ] = None
    beginMonthDay: Optional[
        Annotated[
            str, Meta(description="The beginning month and day for the forecast period")
        ]
    ] = None
    endMonthDay: Optional[
        Annotated[
            str, Meta(description="The ending month and day for the forecast period")
        ]
    ] = None


class ForecastPointDTO(Struct):
    name: Optional[
        Annotated[str, Meta(description="The name of the forecast point")]
    ] = None
    forecaster: Optional[
        Annotated[
            str,
            Meta(
                description="The user name of the forecaster who forecasts for this station"
            ),
        ]
    ] = None
    exceedenceProbabilities: Optional[
        Annotated[
            List[int],
            Meta(description="The name to display in the UI for the profile type"),
        ]
    ] = None


class FunctionDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The function code")]] = None
    abbreviation: Optional[Annotated[str, Meta(description="The abbreviation")]] = None
    name: Optional[Annotated[str, Meta(description="The name")]] = None


class InstrumentDTO(Struct):
    name: Optional[Annotated[str, Meta(description="The instrument name")]] = None
    transducerLength: Optional[
        Annotated[int, Meta(description="The transducer length")]
    ] = None
    dataPrecisionAdjustment: Optional[
        Annotated[int, Meta(description="The data precision adjustment")]
    ] = None
    manufacturer: Optional[Annotated[str, Meta(description="The manufacturer")]] = None
    model: Optional[Annotated[str, Meta(description="The model")]] = None
    active: Optional[Annotated[bool, Meta(description="Is this instrument active")]] = (
        None
    )


class NetworkDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The network code")]] = None
    name: Optional[Annotated[str, Meta(description="The network name")]] = None
    description: Optional[
        Annotated[str, Meta(description="The network description")]
    ] = None


class PhysicalElementDTO(Struct):
    name: Optional[Annotated[str, Meta(description="The physical element name")]] = None
    shefPhysicalElementCode: Optional[
        Annotated[str, Meta(description="The SHEF physical element code")]
    ] = None


class ReservoirMetadataDTO(Struct):
    capacity: Optional[
        Annotated[float, Meta(description="The capacity of the reservoir in acre-feet")]
    ] = None
    elevationAtCapacity: Optional[
        Annotated[
            float,
            Meta(
                description="The elevation of the reservoir (in feet) when it is at capacity"
            ),
        ]
    ] = None
    usableCapacity: Optional[
        Annotated[
            float, Meta(description="The usable capacity of the reservoir in acre-feet")
        ]
    ] = None


class StateDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The state code")]] = None
    fipsNumber: Optional[
        Annotated[str, Meta(description="The state FIPS number code")]
    ] = None
    name: Optional[Annotated[str, Meta(description="The state name")]] = None
    countryCode: Optional[Annotated[str, Meta(description="The country code")]] = None


class DurationName(Enum):
    DAILY = "DAILY"
    HOURLY = "HOURLY"
    SEMIMONTHLY = "SEMIMONTHLY"
    MONTHLY = "MONTHLY"
    CALENDAR_YEAR = "CALENDAR_YEAR"
    WATER_YEAR = "WATER_YEAR"
    INSTANTANEOUS = "INSTANTANEOUS"
    SEASONAL = "SEASONAL"
    DAILY__HOURLY__SEMIMONTHLY__MONTHLY__CALENDAR_YEAR__WATER_YEAR = (
        "DAILY, HOURLY, SEMIMONTHLY, MONTHLY, CALENDAR_YEAR, WATER_YEAR"
    )


class StationElementDTO(Struct):
    elementCode: Optional[Annotated[str, Meta(description="The element code")]] = None
    ordinal: Optional[
        Annotated[int, Meta(description="The ordinal of the station element")]
    ] = None
    heightDepth: Optional[
        Annotated[
            int, Meta(description="The height/depth of the station element in inches")
        ]
    ] = None
    durationName: Optional[
        Annotated[
            DurationName, Meta(description="The duration name of the station element")
        ]
    ] = None
    dataPrecision: Optional[
        Annotated[
            int,
            Meta(description="The data precision of the data for the station element"),
        ]
    ] = None
    storedUnitCode: Optional[
        Annotated[str, Meta(description="The units that the data is stored in")]
    ] = None
    originalUnitCode: Optional[
        Annotated[str, Meta(description="The units that the data was collected in")]
    ] = None
    beginDate: Optional[
        Annotated[
            str,
            Meta(description="The date that the station element was put into service"),
        ]
    ] = None
    endDate: Optional[
        Annotated[
            str,
            Meta(
                description="The date that the station element was taken out of service or 2100-01-01 if still in service"
            ),
        ]
    ] = None
    derivedData: Optional[
        Annotated[
            bool, Meta(description="true/false if the station element data is derived")
        ]
    ] = None


class UnitDTO(Struct):
    code: Optional[Annotated[str, Meta(description="The unit code")]] = None
    singularName: Optional[
        Annotated[str, Meta(description="The singular unit name")]
    ] = None
    pluralName: Optional[Annotated[str, Meta(description="The plural unit name")]] = (
        None
    )
    description: Optional[Annotated[str, Meta(description="The unit description")]] = (
        None
    )


class DataDTO(Struct):
    stationElement: Optional[StationElementDTO] = None
    values: Optional[List[DataValueDTO]] = None
    error: Optional[str] = None


class ForecastDTO(Struct):
    stationTriplet: Optional[
        Annotated[str, Meta(description="The station triplet of the forecast point.")]
    ] = None
    forecastPointName: Optional[
        Annotated[str, Meta(description="The name of the forecast point.")]
    ] = None
    data: Optional[
        Annotated[
            List[ForecastDataDTO],
            Meta(description="Contains forecast data for a forecast point."),
        ]
    ] = None


class ReferenceDataDTO(Struct):
    dcos: Optional[
        Annotated[List[DcoDTO], Meta(description="Contains DCO reference data.")]
    ] = None
    durations: Optional[
        Annotated[
            List[DurationDTO], Meta(description="Contains duration reference data.")
        ]
    ] = None
    elements: Optional[
        Annotated[
            List[ElementDTO], Meta(description="Contains element reference data.")
        ]
    ] = None
    forecastPeriods: Optional[
        Annotated[
            List[ForecastPeriodDTO],
            Meta(description="Contains forecast period reference data."),
        ]
    ] = None
    functions: Optional[
        Annotated[
            List[FunctionDTO], Meta(description="Contains function reference data.")
        ]
    ] = None
    instruments: Optional[
        Annotated[
            List[InstrumentDTO], Meta(description="Contains instrument reference data.")
        ]
    ] = None
    networks: Optional[
        Annotated[
            List[NetworkDTO], Meta(description="Contains network reference data.")
        ]
    ] = None
    physicalElements: Optional[
        Annotated[
            List[PhysicalElementDTO],
            Meta(description="Contains physical element reference data."),
        ]
    ] = None
    states: Optional[
        Annotated[List[StateDTO], Meta(description="Contains State reference data.")]
    ] = None
    units: Optional[
        Annotated[List[UnitDTO], Meta(description="Contains unit reference data.")]
    ] = None


class StationDTO(Struct):
    stationId: Annotated[str, Meta(description="The id of the station")]
    stationTriplet: Optional[
        Annotated[str, Meta(description="The station triplet of the station")]
    ] = None
    stateCode: Optional[
        Annotated[str, Meta(description="The 2-character state code of the station")]
    ] = None
    networkCode: Optional[
        Annotated[str, Meta(description="The network code of the station")]
    ] = None
    name: Optional[Annotated[str, Meta(description="The name of the station")]] = None
    dcoCode: Optional[
        Annotated[str, Meta(description="The DCO code of the station")]
    ] = None
    countyName: Optional[
        Annotated[
            str,
            Meta(description="The name of the county that the station is located in"),
        ]
    ] = None
    huc: Optional[
        Annotated[str, Meta(description="The hydrologic unit code of the station")]
    ] = None
    elevation: Optional[
        Annotated[float, Meta(description="The elevation (in feet) of the station")]
    ] = None
    latitude: Optional[
        Annotated[float, Meta(description="The latitude of the station")]
    ] = None
    longitude: Optional[
        Annotated[float, Meta(description="The longitude of the station")]
    ] = None
    dataTimeZone: Optional[
        Annotated[
            float,
            Meta(
                description="The timezone offset from GMT of the data for the station"
            ),
        ]
    ] = None
    pedonCode: Optional[
        Annotated[str, Meta(description="The NRCS pedon code for the station")]
    ] = None
    shefId: Optional[Annotated[str, Meta(description="The SHEF id of the station")]] = (
        None
    )
    beginDate: Optional[
        Annotated[
            str, Meta(description="The date that the station was put into service")
        ]
    ] = None
    endDate: Optional[
        Annotated[
            str,
            Meta(
                description="The date that the station was taken out of service or 2100-01-01 if still in service"
            ),
        ]
    ] = None
    forecastPoint: Optional[ForecastPointDTO] = None
    reservoirMetadata: Optional[ReservoirMetadataDTO] = None
    stationElements: Optional[
        Annotated[
            List[StationElementDTO],
            Meta(description="The station elements of the station"),
        ]
    ] = None


class StationDataDTO(Struct):
    stationTriplet: Optional[
        Annotated[str, Meta(description="The station triplet of the station")]
    ] = None
    data: Optional[List[DataDTO]] = None
