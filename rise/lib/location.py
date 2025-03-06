# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

from typing import Literal, Optional
from pydantic import BaseModel, field_validator

from rise.lib.types import LocationData, LocationIncluded


class LocationResponse(BaseModel):
    links: Optional[dict[Literal["self", "first", "last", "next"], str]] = None
    meta: Optional[
        dict[
            Literal["totalItems", "itemsPerPage", "currentPage"],
            int,
        ]
    ] = None
    included: list[LocationIncluded]
    data: list[LocationData]

    @field_validator("data", check_fields=True, mode="before")
    @classmethod
    def ensure_list(cls, data: LocationData | list[LocationData]) -> list[LocationData]:
        if not isinstance(data, list):
            return [data]
        return data
