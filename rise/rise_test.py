from rise.lib.cache import RISECache
from rise.lib.helpers import merge_pages
from rise.lib.location import LocationResponse
from rise.rise_edr import RiseEDRProvider


def test_get_all_pages_for_items():
    cache = RISECache("redis")
    all_location_responses = cache.get_or_fetch_all_pages(
        RiseEDRProvider.LOCATION_API
    )
    merged_response = merge_pages(all_location_responses)
    response = LocationResponse(**merged_response)
    assert response