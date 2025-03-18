# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from pytest import FixtureRequest
import pytest
from rise.lib.cache import RISECache
from rise.lib.helpers import await_, merge_pages
from rise.lib.location import LocationResponse
from rise.rise import RiseProvider
from rise.rise_edr import RiseEDRProvider


def test_get_all_pages_for_items():
    cache = RISECache()
    all_location_responses = await_(
        cache.get_or_fetch_all_pages(RiseEDRProvider.LOCATION_API)
    )
    merged_response = merge_pages(all_location_responses)
    response = LocationResponse(**merged_response)
    assert response


@pytest.fixture()
def oaf_config(request: type[FixtureRequest]):
    config = {
        "name": "RISE_EDR_Provider",
        "type": "feature",
        "title_field": "name",
        "cache": "redis",
        "data": "https://data.usbr.gov/rise/api/",
    }
    return config


def test_item(oaf_config: dict):
    """Test what happens if we request one item; make sure the geojson is valid"""
    p = RiseProvider(oaf_config)
    out = p.items(itemId="1")
    out = out
    assert out["id"] == 1
    assert out["type"] == "Feature"

    with pytest.raises(Exception):
        out = p.items(itemId="__INVALID")

    out = p.items(limit=10)
    assert len(out["features"]) == 10


def test_select_properties(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(itemId="1", select_properties=["DUMMY_PROPERTY"])

    assert "locationName" in p._fields, "fields were not set properly"
    outWithSelection = p.items(itemId="1", select_properties=["locationName"])
    out = p.items(itemId="1")
    assert out == outWithSelection

    # make sure that if a location doesn't have a property it doesn't throw an error
    propertyThatIsNullInLocation1 = "locationParentId"
    outWithSelection = p.items(
        itemId="1",
        select_properties=[propertyThatIsNullInLocation1, "locationDescription"],
    )
    assert outWithSelection["features"] == []


def test_properties_key_value_mapping(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(
        itemId="1",
        properties=[("locationName", "DUMMY"), ("locationDescription", "DUMMY")],
    )
    assert out["features"] == []

    out = p.items(
        itemId="1",
        properties=[("_id", "1")],
    )
    assert out["type"] == "Feature"
    assert out["properties"]["_id"] == 1
    out = p.items(
        itemId="1",
        properties=[("_id", "1"), ("locationName", "DUMMY")],
    )
    assert out["features"] == [], (
        f"A filter with a property that doesn't exist should return no results but got {out}"
    )
    allDataOut = p.items(
        properties=[("_id", "1"), ("locationName", "DUMMY")],
    )
    assert allDataOut["features"] == [], (
        f"A filter with a property that doesn't exist should return no results but got {out}"
    )
    assert p.items(
        properties=[("_id", "1")],
    ) == p.items(
        itemId="1",
    ), "Filtering by a property 'id' should be the same as filtering by the item id"


def test_sortby(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(sortby=[{"property": "locationName", "order": "+"}])
    assert out["type"] == "FeatureCollection"

    for i, feature in enumerate(out["features"], start=1):
        prev = out["features"][i - 1]
        curr = feature
        assert prev["properties"]["locationName"] <= curr["properties"]["locationName"]

    # by selecting locationDescription, we know that the value is never None
    # and thus we can always compare to verify order
    out = p.items(
        select_properties=["locationDescription"],
        sortby=[{"property": "locationDescription", "order": "-"}],
    )
    for i, feature in enumerate(out["features"], start=1):
        prev = out["features"][i - 1]
        curr = feature
        assert prev["properties"]["locationDescription"] >= curr["properties"]["locationDescription"]


def test_resulttype_hits(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(resulttype="hits")
    assert len(out["features"]) == 0
    assert out["type"] == "FeatureCollection"
    # make sure numberMatched is greater than 0
    # we can't compare against a constant because it could
    # change but it should always be greater than 0
    assert out["numberMatched"] > 0


def test_skip_geometry(oaf_config: dict):
    p = RiseProvider(oaf_config)
    out = p.items(itemId="1", skip_geometry=True)
    assert out["type"] == "Feature"
    assert out["geometry"] is None
    outWithoutSkip = p.items(itemId="1")
    assert outWithoutSkip["type"] == "Feature"
    assert outWithoutSkip["geometry"]
