
from typing import Literal, Optional 
from pydantic import BaseModel, field_validator

from rise.lib.types.includes import LocationIncluded
from rise.lib.types.main import LocationData




class LocationResponse(BaseModel):
    links: Optional[dict[Literal["self", "first", "last", "next"], str]] = None
    meta: Optional[dict[
        Literal["totalItems", "itemsPerPage", "currentPage"],
        int,
    ]] = None
    included: list[LocationIncluded]
    data: list[LocationData]


    @field_validator("data", check_fields=True, mode="before")
    @classmethod
    def ensure_list(cls, data: LocationData | list[LocationData]) -> list[LocationData]:
        if not isinstance(data, list):
            return [data]
        return data


    def get_catalogItemURLs(
        self
    ) -> dict[str, list[str]]:
        locationIdToCatalogRecord: dict[str, str] = {}

        catalogRecordToCatalogItems: dict[str, list[str]] = {}

        for included_item in self.included:
            if included_item.type == "CatalogRecord":
                catalogRecord = included_item.id
                locationId = included_item.relationships.location
                assert locationId is not None
                locationId = locationId.data[0]["id"]
                locationIdToCatalogRecord[locationId] = catalogRecord
            elif included_item.type == "CatalogItem":
                catalogItem = included_item.id
                catalogRecord = included_item.relationships.catalogRecord
                assert catalogRecord is not None
                catalogRecord = catalogRecord.data[0]["id"]
                if catalogRecord not in catalogRecordToCatalogItems:
                    catalogRecordToCatalogItems[catalogRecord] = []
                catalogRecordToCatalogItems[catalogRecord].append(catalogItem)

        join: dict[str, list[str]] = {}
        for locationId, catalogRecord in locationIdToCatalogRecord.items():
            if catalogRecord in catalogRecordToCatalogItems:
                for catalogItem in catalogRecordToCatalogItems[catalogRecord]:
                    catalogItemURL = f"https://data.usbr.gov{catalogItem}"
                    if locationId not in join:
                        join[str(locationId)] = [catalogItemURL]
                    else:
                        join[locationId].append(catalogItemURL)

        return join
