# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from awdb_forecasts.lib.locations import ForecastLocationCollection


def test_generate_collection_with_forecast_metadata():
    fc = ForecastLocationCollection()
    assert fc
