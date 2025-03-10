# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import os
import requests

requests.packages.urllib3.util.connection.HAS_IPV6 = False

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
