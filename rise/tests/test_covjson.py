# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import requests
from rise.cache import RISECache
from rise.covjson import CovJSONBuilder
from rise.custom_types import LocationResponse


def test_one_location():
    headers = {"accept": "application/vnd.api+json"}
    r: LocationResponse = requests.get(
        "https://data.usbr.gov/rise/api/location/1?page=1&itemsPerPage=5&include=catalogRecords.catalogItems",
        headers=headers,
    ).json()

    cache = RISECache()

    CovJSONBuilder(cache).render(r)
