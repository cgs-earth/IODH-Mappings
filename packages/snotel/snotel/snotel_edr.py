# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import logging
from typing import Optional

from com.helpers import EDRField
from pygeoapi.provider.base_edr import BaseEDRProvider
from snotel.lib.parameters import ParametersCollection

LOGGER = logging.getLogger(__name__)


class SnotelEDRProvider(BaseEDRProvider):
    """The EDR Provider for the Snotel API"""

    def __init__(self, provider_def=None):
        """
        Initialize object

        :param provider_def: provider definition

        :returns: rise.base_edr.RiseEDRProvider
        """
        super().__init__(provider_def)

        self.instances = []

    @BaseEDRProvider.register()
    def locations(
        self,
        location_id: Optional[str] = None,
        datetime_: Optional[str] = None,
        select_properties: Optional[list[str]] = None,
        crs: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract data from location
        """
        ...

    def get_fields(self) -> dict[str, EDRField]:
        """Get the list of all parameters (i.e. fields) that the user can filter by"""
        if not self._fields:
            self._fields = ParametersCollection().get_fields()
        return self._fields

    @BaseEDRProvider.register()
    def cube(
        self,
        bbox: list,
        datetime_: Optional[str] = None,
        select_properties: Optional[list] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Returns a data cube defined by bbox and z parameters

        :param bbox: `list` of minx,miny,maxx,maxy coordinate values as `float`
        :param datetime_: temporal (datestamp or extent)
        :param z: vertical level(s)
        :param format_: data format of output
        """
        ...

    @BaseEDRProvider.register()
    def area(
        self,
        # Well known text (WKT) representation of the geometry for the area
        wkt: str,
        select_properties: list[str] = [],
        datetime_: Optional[str] = None,
        z: Optional[str] = None,
        format_: Optional[str] = None,
        **kwargs,
    ):
        """
        Extract and return coverage data from a specified area.
        """
        ...

    @BaseEDRProvider.register()
    def items(self, **kwargs):
        # We have to define this since pygeoapi has a limitation and needs both EDR and OAF for items
        # https://github.com/geopython/pygeoapi/issues/1748
        pass
