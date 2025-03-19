from typing import Literal, NotRequired, TypedDict

class GeojsonFeature(TypedDict):
    type: Literal["Feature"]
    geometry: dict 
    properties: dict
    id: int

class GeojsonResponseDict(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[GeojsonFeature]
    numberMatched: NotRequired[int]