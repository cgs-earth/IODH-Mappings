# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from rise.lib.covjson.template import COVJSON_TEMPLATE
from rise.lib.covjson.types.covjson import (
    CoverageCollection,
    Coverage,
    CoverageRange,
    Parameter,
)
from rise.lib.cache import RISECache
from rise.lib.location import LocationData
from rise.lib.location_with_results import LocationResponseWithResults

LOGGER = logging.getLogger(__name__)


def _generate_coverage_item(
    paramToCoverage: dict[str, CoverageRange],
    location_feature: LocationData,
    times: list[str],
) -> Coverage:
    # if it is a point it will have different geometry
    isPoint = location_feature.attributes.locationCoordinates.type == "Point"

    if isPoint:
        # z = location_feature["attributes"]["elevation"]
        coords = location_feature.attributes.locationCoordinates.coordinates
        x, y = coords[0], coords[1]

        coverage_item: Coverage = {
            "type": "Coverage",
            "domainType": "PointSeries",
            "domain": {
                "type": "Domain",
                "axes": {
                    "x": {"values": [x]},
                    "y": {"values": [y]},
                    "t": {"values": times},
                },
            },
            "ranges": paramToCoverage,
        }

    else:
        coverage_item: Coverage = {
            "type": "Coverage",
            "domainType": "PolygonSeries",
            "domain": {
                "type": "Domain",
                "axes": {
                    "composite": {
                        "dataType": location_feature.attributes.locationCoordinates.type,
                        "coordinates": ["x", "y"],
                        "values": [
                            location_feature.attributes.locationCoordinates.coordinates
                        ],
                    },
                    "t": {"values": times},
                },
            },
            "ranges": paramToCoverage,
        }

    return coverage_item


class CovJSONBuilder:
    """A helper class for building CovJSON from a Rise JSON Response"""

    _cache: RISECache  # The RISE Cache to use for storing and fetching data

    def __init__(self, cache: RISECache):
        self._cache = cache

    def _get_relevant_parameters(self, location_response: LocationResponseWithResults) -> set[str]:
        relevant_parameters = set()
        for location_feature in location_response.data:
            for param in location_feature.relationships.catalogItems.data:
                id = str(param["attributes"]["parameterId"])
                relevant_parameters.add(id)
        return relevant_parameters

    def _get_parameter_metadata(self, location_response: LocationResponseWithResults):
        relevant_parameters = self._get_relevant_parameters(location_response)

        paramNameToMetadata: dict[str, Parameter] = {}

        paramsToGeoJsonOutput = self._cache.get_or_fetch_parameters()
        for param_id in paramsToGeoJsonOutput:
            if relevant_parameters and param_id not in relevant_parameters:
                continue

            associatedData = paramsToGeoJsonOutput[param_id]

            _param: Parameter = {
                "type": "Parameter",
                "description": {"en": associatedData["description"]},
                "unit": {"symbol": associatedData["x-ogc-unit"]},
                "observedProperty": {
                    "id": param_id,
                    "label": {"en": associatedData["title"]},
                },
            }
            # TODO check default if _id isn't present

            natural_language_name = associatedData["title"]
            paramNameToMetadata[natural_language_name] = _param

        return paramNameToMetadata

    def _get_coverages(self, location_response: LocationResponseWithResults) -> list[Coverage]:
        """Return the data needed for the 'coverage' key in the covjson response"""
        coverages: list[Coverage] = []

        for location_feature in location_response.data:
            # CoverageJSON needs a us to associated every parameter with data
            # This data is grouped independently for each location
            paramToCoverage: dict[str, CoverageRange] = {}

            for param in location_feature.relationships.catalogItems.data:
                if not (  # ensure param contains data so it can be used for covjson
                    param["results"] is not None
                    and len(param["results"]) > 0
                    and param["results"][0]["attributes"] is not None
                ):
                    # Since coveragejson does not allow a parameter without results,
                    # we can skip adding the parameter/location combination all together
                    continue

                results: list[float] = [
                    result["attributes"]["result"] for result in param["results"]
                ]
                times: list[str] = [
                    result["attributes"]["dateTime"] for result in param["results"]
                ]

                # id = str(param["attributes"]["parameterId"])
                id = param["attributes"]["parameterName"]

                paramToCoverage[id] = {
                    "axisNames": ["t"],
                    "dataType": "float",
                    "shape": [len(results)],
                    "values": results,
                    "type": "NdArray",
                }

                coverage_item = _generate_coverage_item(
                    paramToCoverage, location_feature, times
                )

                coverages.append(coverage_item)
        return coverages

    def fill_template(
        self, location_response: LocationResponseWithResults
    ) -> CoverageCollection:
        templated_covjson: CoverageCollection = COVJSON_TEMPLATE
        templated_covjson["coverages"] = self._get_coverages(location_response)
        templated_covjson["parameters"] = self._get_parameter_metadata(
            location_response=location_response
        )

        return templated_covjson
