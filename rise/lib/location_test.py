# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
from rise.lib.cache import RISECache
from rise.lib.helpers import flatten_values, getResultUrlFromCatalogUrl, await_
from rise.lib.location import LocationResponseWithIncluded


@pytest.fixture
def oneItemLocationRespFixture():
    url = "https://data.usbr.gov/rise/api/location/1?include=catalogRecords.catalogItems&page=1&itemsPerPage=5"
    cache = RISECache()
    resp = await_(cache.get_or_fetch(url))
    return resp


def test_get_catalogItemURLs(oneItemLocationRespFixture: dict):
    """Test getting the associated catalog items from the location response"""
    model = LocationResponseWithIncluded.model_validate(oneItemLocationRespFixture)
    urls = model.get_catalogItemURLs()
    for url in [
        "https://data.usbr.gov/rise/api/catalog-item/4222",
        "https://data.usbr.gov/rise/api/catalog-item/4223",
        "https://data.usbr.gov/rise/api/catalog-item/4225",
    ]:
        assert url in urls["/rise/api/location/1"]


def test_associated_results_have_data(oneItemLocationRespFixture: dict):
    cache = RISECache()
    model = LocationResponseWithIncluded.model_validate(oneItemLocationRespFixture)
    urls = model.get_catalogItemURLs()
    for url in urls:
        resultUrl = getResultUrlFromCatalogUrl(url, datetime_=None)
        resp = await_(cache.get_or_fetch(resultUrl))
        assert resp["data"], resp["data"]


def test_filter_by_wkt(oneItemLocationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(oneItemLocationRespFixture)
    squareInOcean = "POLYGON ((-70.64209 40.86368, -70.817871 37.840157, -65.236816 38.013476, -65.500488 41.162114, -70.64209 40.86368))"
    emptyModel = model.drop_outside_of_wkt(squareInOcean)
    assert emptyModel.data == []
    entireUS = "POLYGON ((-144.492188 57.891497, -146.25 11.695273, -26.894531 12.382928, -29.179688 59.977005, -144.492188 57.891497))"
    fullModel = model.drop_outside_of_wkt(entireUS)
    assert len(fullModel.data) == len(model.data)


def test_drop_locationid(oneItemLocationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(oneItemLocationRespFixture)
    # since the fixture is for location 1, make sure that if we drop location 1 everything is gone
    droppedModel = model.drop_specific_location(location_id=1)
    assert len(droppedModel.data) == 0

    sameModel = model.drop_specific_location(location_id=2)
    assert len(sameModel.data) == len(model.data)


@pytest.fixture
def allItemsOnePageLocationRespFixture():
    url = "https://data.usbr.gov/rise/api/location?&include=catalogRecords.catalogItems?page=1&itemsPerPage=100"
    cache = RISECache()
    resp = await_(cache.get_or_fetch(url))
    return resp


def test_get_all_catalogItemURLs(allItemsOnePageLocationRespFixture: dict):
    model = LocationResponseWithIncluded.model_validate(
        allItemsOnePageLocationRespFixture
    )
    urls = flatten_values(model.get_catalogItemURLs())
    assert len(urls) > 400
