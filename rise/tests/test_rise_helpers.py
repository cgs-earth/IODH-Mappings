from datetime import timedelta
import json
import logging

import redis

from rise.rise_edr_share import merge_pages
import pytest
import shapely.wkt

from pygeoapi.provider.base import ProviderQueryError
from rise.rise_edr_helpers import (
    LocationHelper,
    flatten_values,
    getResultUrlFromCatalogUrl,
    parse_bbox,
    parse_z,
    ZType,
)

from rise.rise_cache import RISECache, fetch_url

import shapely

import asyncio

import requests
import time

LOGGER = logging.getLogger(__name__)


def test_get_catalogItems():
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)
        items = LocationHelper.get_catalogItemURLs(data)
        assert len(items) == 25


def test_fetch():
    url = "https://data.usbr.gov/rise/api/catalog-item/128562"
    resp = requests.get(
        url,
        headers={"accept": "application/vnd.api+json"},
    )
    assert resp.json()

    async_resp = asyncio.run(fetch_url(url))
    assert async_resp == resp.json()


def test_remove_location():
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)
        dropped = LocationHelper.drop_location(data, 6902)
        assert len(data["data"]) - 1 == len(dropped["data"])
        assert dropped["data"][0]["attributes"]["_id"] != 6902


def test_merge_pages():
    fetched_mock = {
        "https://data.usbr.gov/rise/api/location2": {
            "data": [
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128564"},
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128565"},
            ]
        },
        "https://data.usbr.gov/rise/api/location1": {
            "data": [
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128562"},
                {"id": "https://data.usbr.gov/rise/api/catalog-item/128563"},
            ]
        },
    }

    merged = merge_pages(fetched_mock)
    for url, content in merged.items():
        assert content is not None
        assert content["data"]
        assert len(content["data"]) == 4


@pytest.mark.parametrize("cache_type", ["redis", "shelve"])
def test_integration_merge_pages(cache_type):
    url = "https://data.usbr.gov/rise/api/location"

    totalitems = requests.get(
        url, headers={"accept": "application/vnd.api+json"}
    ).json()["meta"]["totalItems"]

    cache = RISECache(cache_type)
    pages = cache.get_or_fetch_all_pages(url, force_fetch=True)
    merged = merge_pages(pages)
    for url, content in merged.items():
        assert content is not None
        assert content["data"]
        assert len(content["data"]) == totalitems
        break


@pytest.mark.parametrize("cache_type", ["redis", "shelve"])
def test_fetch_all_only_fetches_one_if_one_page(cache_type):
    url = "https://data.usbr.gov/rise/api/location/1"
    cache = RISECache(cache_type)
    pages = cache.get_or_fetch_all_pages(url, force_fetch=True)
    assert len(pages) == 1

    res = requests.get(url, headers={"accept": "application/vnd.api+json"}).json()
    assert res["data"] == pages[url]["data"]


def test_z_parse():
    assert (ZType.SINGLE, [10]) == parse_z("10")
    assert (ZType.RANGE, [10, 20]) == parse_z("10/20")
    assert (ZType.ENUMERATED_LIST, [10, 20, 30]) == parse_z("10,20,30")

    assert (ZType.ENUMERATED_LIST, [100, 150]) == parse_z("R2/100/50")

    with pytest.raises(ProviderQueryError):
        parse_z("10/20/30")

    with pytest.raises(ProviderQueryError):
        parse_z("10//30")

    with pytest.raises(ProviderQueryError):
        parse_z("10,20,30,")


def test_shapely_sanity_check():
    geo: dict = {
        "type": "Point",
        "coordinates": [-104.855255, 39.651378],
    }

    result = shapely.geometry.shape(geo)

    wkt = "POLYGON((-79 40,-79 38,-75 38,-75 41,-79 40))"

    wkt_parsed = shapely.wkt.loads(wkt)
    assert not wkt_parsed.contains(result)

    assert int(float("4530.000000")) == 4530
    location_6902_geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [-111.49544, 36.94029],
                [-111.49544, 36.99597],
                [-111.47861, 36.99597],
                [-111.47861, 36.94029],
                [-111.49544, 36.94029],
            ]
        ],
    }

    point_inside = "POINT(-111.48 36.95)"
    point_inside = shapely.wkt.loads(point_inside)

    assert shapely.geometry.shape(location_6902_geom).contains(point_inside)

    point_outside = "POINT(-111.5 46.95)"
    point_outside = shapely.wkt.loads(point_outside)

    assert not shapely.geometry.shape(location_6902_geom).contains(point_outside)


def test_wkt_filter():
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)

        res = LocationHelper.filter_by_wkt(data, wkt=None, z="4530")

        assert res["data"][0]["attributes"]["_id"] == 6888
        assert len(res["data"]) == 1
        wkt = "POLYGON((-79 40,-79 38,-75 38,-75 41,-79 40))"

        # Query that should not return anything
        res = LocationHelper.filter_by_wkt(data, wkt, z="4530")

        assert len(res["data"]) == 0

        locations_inside_this = "POINT(-106.849378 33.821858)"

        res = LocationHelper.filter_by_wkt(data, wkt=locations_inside_this, z=None)
        assert len(res["data"]) == 1
        assert res["data"][0]["attributes"]["_id"] == 6888

        locations_inside_this = (
            "POLYGON((-150 -150,-150 150,150 150,150 -150,-150 -150))"
        )
        # all locations should be returned if we have a
        res = LocationHelper.filter_by_wkt(data, wkt=locations_inside_this, z=None)
        assert len(res["data"]) == 25


def test_parse_bbox():
    bbox = ["-6.0", "50.0", "-4.35", "52.0"]
    parse_result = parse_bbox(bbox)
    shapely_bbox = parse_result[0]
    assert shapely_bbox
    zval = parse_result[1]
    assert not zval

    wkt = "POINT(-5.0 51)"
    single_point = shapely.wkt.loads(wkt)

    parse_result = parse_bbox(bbox)
    if parse_result[0]:
        assert parse_result[0].contains(single_point)
    else:
        assert False


def test_limit_items():
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)

        res1 = LocationHelper.filter_by_limit(data, limit=1)
        assert len(res1["data"]) == 1

        res2 = LocationHelper.filter_by_limit(data, limit=10)
        assert len(res2["data"]) == 10
        assert (
            res2["data"][0]["attributes"]["_id"] == res1["data"][0]["attributes"]["_id"]
        )


def test_filter_by_id():
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)

        res = LocationHelper.filter_by_id(data, identifier="6902")
        assert res["data"][0]["attributes"]["_id"] == 6902

        res = LocationHelper.filter_by_id(data, identifier="6903")
        assert len(res["data"]) == 0


def test_get_or_fetch_group():
    group = [
        "https://data.usbr.gov/rise/api/catalog-item/128632",
        "https://data.usbr.gov/rise/api/location?page=1&itemsPerPage=25",
    ]

    cache = RISECache()
    urlToContent = asyncio.run(cache.get_or_fetch_group(group))

    assert len(urlToContent.values()) == 2
    # Can't do a better test here since the remote value changes ocassionally and can make this flakey
    assert urlToContent[group[1]]["data"][0]["id"] is not None


def test_make_result():
    url = "https://data.usbr.gov/rise/api/catalog-item/128632"
    res = getResultUrlFromCatalogUrl(url, None)
    resp = requests.get(res)
    assert resp.ok


def test_redis():
    r = redis.Redis(host="redis", port=6379, db=0)
    assert r
    r.set("test", "test")
    val = r.get("test")
    assert val == b"test"


def test_simple_redis_serialization():
    cache = RISECache("redis")
    with open("rise/tests/data/location.json") as f:
        data = json.load(f)
        cache.set("test_url_location", data, timedelta(milliseconds=1000))
        # our interface does not export an atomic set operation, so we need to just block heuristically
        time.sleep(0.2)
        val = cache.get("test_url_location")
        assert val == data


def test_redis_wrapper():
    cache = RISECache("redis")
    cache.clear("test_url_catalog_item")
    cache.set("test_url_catalog_item", {}, timedelta(milliseconds=1000))
    assert cache.get("test_url_catalog_item") == {}
    time.sleep(1)
    with pytest.raises(KeyError):
        cache.get("test_url_catalog_item")


@pytest.mark.parametrize("cache_type", ["redis", "shelve"])
class TestFnsWithCaching:
    def test_fetch_group(self, cache_type):
        urls = [
            "https://data.usbr.gov/rise/api/catalog-item/128562",
            "https://data.usbr.gov/rise/api/catalog-item/128563",
            "https://data.usbr.gov/rise/api/catalog-item/128564",
        ]
        cache = RISECache(cache_type)
        resp = asyncio.run(cache.fetch_and_set_url_group(urls))
        assert len(resp) == 3
        assert None not in resp

    def test_get_parameters(self, cache_type):
        with open("rise/tests/data/location.json") as f:
            data = json.load(f)
            items = LocationHelper.get_catalogItemURLs(data)
            assert len(items) == 25
            assert len(flatten_values(items)) == 236

        with open("rise/tests/data/location.json") as f:
            data = json.load(f)
            cache = RISECache(cache_type)
            locationsToParams = LocationHelper.get_parameters(data, cache)
            assert len(locationsToParams.keys()) > 0
            # Test it contains a random catalog item from the location
            assert cache.contains("https://data.usbr.gov/rise/api/catalog-item/128573")
            assert "18" in flatten_values(locationsToParams)  # type: ignore

    # def test_get_parameters_full_catalog(self, cache_type):
    #     """Stress test for get_parameters"""
    #     response = requests.get(
    #         "https://data.usbr.gov/rise/api/location",
    #         headers={"accept": "application/vnd.api+json"},
    #     ).json()
    #     cache = RISECache(cache_type)
    #     locationsToParams = LocationHelper.get_parameters(response, cache)

    def test_fetch_all_pages(self, cache_type):
        url = "https://data.usbr.gov/rise/api/location"
        cache = RISECache(cache_type)
        pages = cache.get_or_fetch_all_pages(url)

        # There are 6 pages so we should get 6 responses
        assert len(pages) == 6
        for url, resp in pages.items():
            # 100 is the max number of items you can query
            # so we should get 100 items per page
            assert resp["meta"]["itemsPerPage"] == 100

    def test_fields_are_unique(self, cache_type):
        cache = RISECache(cache_type)
        field_ids = cache.get_or_fetch_parameters().keys()
        length = len(field_ids)
        assert length == len(set(field_ids))

    def test_expand_with_results(self, cache_type):
        with open("rise/tests/data/location.json") as f:
            data = json.load(f)

            # filter just 268 which contains catalog item 4 which has results
            res = LocationHelper.filter_by_id(data, identifier="268")
            cache = RISECache(cache_type)
            expanded = LocationHelper.fill_catalogItems(res, cache, add_results=True)

            assert expanded["data"][0]["relationships"]["catalogItems"] is not None

            assert (
                len(expanded["data"][0]["relationships"]["catalogItems"]["data"]) == 5
            )

        ids = [
            item["id"]
            for item in expanded["data"][0]["relationships"]["catalogItems"]["data"]
        ]
        assert "/rise/api/catalog-item/4" in ids
        assert "/rise/api/catalog-item/141" in ids
        assert "/rise/api/catalog-item/142" in ids
        assert "/rise/api/catalog-item/144" in ids
        assert "/rise/api/catalog-item/11279" in ids

    def test_cache(self, cache_type):
        url = "https://data.usbr.gov/rise/api/catalog-item/128562"

        start = time.time()
        cache = RISECache(cache_type)
        cache.clear(url)
        remote_res = asyncio.run(cache.get_or_fetch(url))
        assert remote_res
        network_time = time.time() - start

        assert cache.contains(url)

        start = time.time()
        cache.clear(url)
        assert not cache.contains(url)
        disk_res = asyncio.run(cache.get_or_fetch(url))
        assert disk_res
        disk_time = time.time() - start

        assert remote_res == disk_res
        assert disk_time < network_time

    def test_fill_catalogItems(self, cache_type):
        with open("rise/tests/data/location.json") as f:
            data = json.load(f)
            assert len(data["data"]) == 25

            res = LocationHelper.filter_by_id(data, identifier="6902")
            assert res["data"][0]["attributes"]["_id"] == 6902
            assert len(res["data"]) == 1
            assert (
                res["data"][0]["relationships"]["catalogItems"]["data"][0]["id"]
                == "/rise/api/catalog-item/128632"
            ), print(res["data"][0]["relationships"]["catalogItems"])

            # Fill in the catalog items and make sure that the only two
            # remaining catalog items are the catalog items associated with location
            # 6902 since we previously filtered to just that location
            cache = RISECache(cache_type)
            expanded = LocationHelper.fill_catalogItems(res, cache)

            assert expanded["data"][0]["relationships"]["catalogItems"] is not None

            assert (
                len(expanded["data"][0]["relationships"]["catalogItems"]["data"]) == 2
            )

            # Expanded is flakey and can return in either order, so we just check both
            assert (
                expanded["data"][0]["relationships"]["catalogItems"]["data"][0]["id"]
                == "/rise/api/catalog-item/128632"
                or expanded["data"][0]["relationships"]["catalogItems"]["data"][0]["id"]
                == "/rise/api/catalog-item/128633"
            )
            assert (
                expanded["data"][0]["relationships"]["catalogItems"]["data"][1]["id"]
                == "/rise/api/catalog-item/128633"
                or expanded["data"][0]["relationships"]["catalogItems"]["data"][1]["id"]
                == "/rise/api/catalog-item/128632"
            )

    def test_cache_clears(self, cache_type):
        cache = RISECache(cache_type)
        cache.set(
            "https://data.usbr.gov/rise/api/catalog-item/128562", {"data": "test"}
        )
        assert asyncio.run(
            cache.get_or_fetch("https://data.usbr.gov/rise/api/catalog-item/128562")
        ) == {"data": "test"}

        cache.clear("https://data.usbr.gov/rise/api/catalog-item/128562")
        time.sleep(1)
        assert (
            cache.contains("https://data.usbr.gov/rise/api/catalog-item/128562")
            is False
        )
        with pytest.raises(KeyError):
            cache.get("https://data.usbr.gov/rise/api/catalog-item/128562")
