# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests
from rise.lib.cache import RISECache
from rise.lib.helpers import getResultUrlFromCatalogUrl, safe_run_async
from rise.lib.location import LocationResponseWithIncluded


@pytest.fixture
def locationRespFixture():
    url = "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    resp = requests.get(url, headers={"accept": "application/vnd.api+json"})
    assert resp.ok, resp.text
    return resp.json()


def test_get_catalogItemURLs(locationRespFixture: dict):
    """Test getting the associated catalog items from the location response"""
    model = LocationResponseWithIncluded.model_validate(locationRespFixture)
    urls = model.get_catalogItemURLs()
    for url in [
        "https://data.usbr.gov/rise/api/catalog-item/4222",
        "https://data.usbr.gov/rise/api/catalog-item/4223",
        "https://data.usbr.gov/rise/api/catalog-item/4225",
    ]:
        assert url in urls["/rise/api/location/1"]


def test_associated_results_have_data(locationRespFixture: dict):
    cache = RISECache("redis")
    model = LocationResponseWithIncluded.model_validate(locationRespFixture)
    urls = model.get_catalogItemURLs()
    for url in urls:
        resultUrl = getResultUrlFromCatalogUrl(url, datetime_=None)
        resp = safe_run_async(cache.get_or_fetch(resultUrl))
        assert resp["data"], resp["data"]


def test_filter_by_wkt(locationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(locationRespFixture)
    squareInOcean = "POLYGON ((-70.64209 40.86368, -70.817871 37.840157, -65.236816 38.013476, -65.500488 41.162114, -70.64209 40.86368))"
    emptyModel = model.filter_by_wkt(squareInOcean)
    assert emptyModel.data == []
    entireUS = "POLYGON ((-144.492188 57.891497, -146.25 11.695273, -26.894531 12.382928, -29.179688 59.977005, -144.492188 57.891497))"
    fullModel = model.filter_by_wkt(entireUS)
    assert len(fullModel.data) == len(model.data)


def test_drop_locationid(locationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(locationRespFixture)
    # since the fixture is for location 1, make sure that if we drop location 1 everything is gone
    droppedModel = model.drop_location(location_id=1)
    assert len(droppedModel.data) == 0

    sameModel = model.drop_location(location_id=2)
    assert len(sameModel.data) == len(model.data)
