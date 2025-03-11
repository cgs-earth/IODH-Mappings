
import asyncio
from datetime import timedelta
import json
import time

import pytest
from rise.lib.cache import RISECache
from rise.lib.helpers import safe_run_async


def test_simple_redis_serialization():
    cache = RISECache("redis")

    data = json.loads("{\"test\": 1}")
    cache.set("test_url_location", data, timedelta(milliseconds=1000))  # noqa: F821
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

class TestFnsWithCaching:
    def test_fetch_group(self):
        urls = [
            "https://data.usbr.gov/rise/api/catalog-item/128562",
            "https://data.usbr.gov/rise/api/catalog-item/128563",
            "https://data.usbr.gov/rise/api/catalog-item/128564",
        ]
        cache = RISECache("redis")
        resp = safe_run_async(cache.fetch_and_set_url_group(urls))
        assert len(resp) == 3
        assert None not in resp

    def test_fetch_all_pages(self):
        url = "https://data.usbr.gov/rise/api/location"
        cache = RISECache("redis")
        pages = cache.get_or_fetch_all_pages(url)

        # this is at least 7 since in the future the api could change
        assert len(pages) >= 7, "Expected at least 7 pages"
        for url, resp in pages.items():
            # 100 is the max number of items you can query
            # so we should get 100 items per page
            assert resp["meta"]["itemsPerPage"] == 100

    def test_fields_are_unique(self):
        cache = RISECache("redis")
        field_ids = cache.get_or_fetch_parameters().keys()
        length = len(field_ids)
        assert length == len(set(field_ids))

    def test_cache(self):
        url = "https://data.usbr.gov/rise/api/catalog-item/128562"

        cache = RISECache("redis")
        cache.clear(url)
        remote_res = safe_run_async(cache.get_or_fetch(url))

        assert cache.contains(url)

        cache.clear(url)
        assert not cache.contains(url)
        disk_res = safe_run_async(cache.get_or_fetch(url))
        assert disk_res
        assert remote_res == disk_res

    def test_cache_clears(self):
        cache = RISECache("redis")
        cache.set(
            "https://data.usbr.gov/rise/api/catalog-item/128562", {"data": "test"}
        )
        assert safe_run_async(
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


def test_safe_async():
    # Create an event loop without running anything on it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Check that the event loop is running by calling run_async
    safe_run_async(asyncio.sleep(0.1))

    # Close the event loop after the test
    loop.close()
