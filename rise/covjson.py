from typing import Optional
from rise.rise_api_types import (
    CoverageCollection,
    Coverage,
    CoverageRange,
    LocationData,
    LocationResponse,
    Parameter,
)
from rise.rise_cache import RISECache
from rise.rise_edr_helpers import LocationHelper

COVJSON_TEMPLATE: CoverageCollection = {
    "type": "CoverageCollection",
    ## CoverageJSON makes us specify a list of parameters that are relevant for the entire coverage collection
    "parameters": {},
    "referencing": [
        {
            "coordinates": ["x", "y"],
            "system": {
                "type": "GeographicCRS",
                "id": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            },
        },
        {
            "coordinates": ["z"],
            "system": {
                "type": "VerticalCRS",
                "cs": {
                    "csAxes": [
                        {
                            "name": {"en": "Pressure"},
                            "direction": "down",
                            "unit": {"symbol": "Pa"},
                        }
                    ]
                },
            },
        },
        {
            "coordinates": ["t"],
            "system": {"type": "TemporalRS", "calendar": "Gregorian"},
        },
    ],
    "coverages": {},  # type: ignore this w/ static type checks since it is a template
}


def generate_coverage_item(
    paramToCoverage: dict[str, CoverageRange],
    location_feature: LocationData,
    times: list[str],
) -> Coverage:
    # if it is a point it will have different geometry
    isPoint = location_feature["attributes"]["locationCoordinates"]["type"] == "Point"

    if isPoint:
        # z = location_feature["attributes"]["elevation"]
        coords = location_feature["attributes"]["locationCoordinates"]["coordinates"]
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
                        "dataType": location_feature["attributes"][
                            "locationCoordinates"
                        ]["type"],
                        "coordinates": ["x", "y"],
                        "values": [
                            location_feature["attributes"]["locationCoordinates"][
                                "coordinates"
                            ]
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

    _locationResponse: (
        LocationResponse  # The response from RISE conforming to the /locations response
    )
    _cache: RISECache  # The RISE Cache to use for storing and fetching data
    _coverages: list[Coverage]
    _time_filter: Optional[
        str  # When converting from a RISE locationresponse to covjson we fetch results. We can filter by time here
    ]
    _params_with_metadata: dict

    def __init__(
        self,
        cache: RISECache,
        locationResponse: LocationResponse,
        time_filter: Optional[str] = None,
    ):
        self._cache = cache
        self._locationResponse = LocationHelper.fill_catalogItems(
            locationResponse, cache, time_filter, add_results=True
        )
        return self

    def _get_relevant_parameters(self) -> set[str]:
        relevant_parameters = set()
        for location_feature in self._locationResponse["data"]:
            for param in location_feature["relationships"]["catalogItems"]["data"]:
                id = str(param["attributes"]["parameterId"])
                relevant_parameters.add(id)
        return relevant_parameters

    def fill_parameters(self, only_include_ids: Optional[list[str]] = None) -> None:
        relevant_parameters = self._get_relevant_parameters()

        paramIdsToMetadata: dict[str, Parameter] = {}

        paramsToGeoJsonOutput = self._cache.get_or_fetch_parameters()
        for f in paramsToGeoJsonOutput:
            if only_include_ids and f not in only_include_ids:
                continue

            associatedData = paramsToGeoJsonOutput[f]

            _param: Parameter = {
                "type": "Parameter",
                "description": {"en": associatedData["description"]},
                "unit": {"symbol": associatedData["x-ogc-unit"]},
                "observedProperty": {
                    "id": f,
                    "label": {"en": associatedData["title"]},
                },
            }
            # TODO check default if _id isn't present
            paramIdsToMetadata[f] = _param

        self._params_with_metadata = paramIdsToMetadata

    def fill_coverages(self) -> None:
        for location_feature in self._locationResponse["data"]:
            # CoverageJSON needs a us to associated every parameter with data
            # This data is grouped independently for each location
            paramToCoverage: dict[str, CoverageRange] = {}

            for param in location_feature["relationships"]["catalogItems"]["data"]:
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

                id = str(param["attributes"]["parameterId"])

                paramToCoverage[id] = {
                    "axisNames": ["t"],
                    "dataType": "float",
                    "shape": [len(results)],
                    "values": results,
                    "type": "NdArray",
                }

                coverage_item = generate_coverage_item(
                    paramToCoverage, location_feature, times
                )

                self._coverages.append(coverage_item)

    def render(self) -> CoverageCollection:
        templated_covjson: CoverageCollection = COVJSON_TEMPLATE
        templated_covjson["coverages"] = self._coverages
        templated_covjson["parameters"] = self._params_with_metadata

        return templated_covjson
