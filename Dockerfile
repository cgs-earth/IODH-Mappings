# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

FROM geopython/pygeoapi:latest

WORKDIR /pygeoapi

# Install the additional requirements for the RISE mapping
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements-rise.txt
RUN pygeoapi openapi generate /pygeoapi/local.config.yml --output-file /pygeoapi/local.openapi.yml

### Below is used for hot reloading; remove the below lines for standard production pygeoapi
ENTRYPOINT [ "pygeoapi", "serve" ]
###
