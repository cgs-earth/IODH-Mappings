# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def setup_before_tests():
    requests.packages.urllib3.util.connection.HAS_IPV6 = False
