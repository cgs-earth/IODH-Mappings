from com.cache import RedisCache
import pytest
from snotel.lib.states import US_STATE_ABBREVIATIONS


@pytest.mark.upstream
@pytest.mark.asyncio
async def test_element_filter():
    """
    It appears that in some cases, filtering by elements does not do anything

    This is unusual behavior and might be a sign something is wrong upstream
    """
    cache = RedisCache()

    triplets = ""
    for state in US_STATE_ABBREVIATIONS:
        triplets += f"*:{state}:SNTL,"

    baseUrl = f"https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&stationTriplets={triplets}"

    response = await cache.get_or_fetch(baseUrl)

    reponseWithoutCommaSeparatedStates = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true&stationTriplets=*:*:SNTL"

    responseWithoutCommaSeparatedStates = await cache.get_or_fetch(
        reponseWithoutCommaSeparatedStates
    )

    """
    According to upstream swagger docs

    'The list of stations will be filtered to only those that contain at least one of the elements specified and the list of stations elements will be filter to only those that have these elements.'
    """

    urlWithFilter = f"{baseUrl}&elements=TAVG"

    responseWithFilter = await cache.get_or_fetch(urlWithFilter)

    assert len(response) == len(responseWithFilter)
    assert len(response) == len(responseWithoutCommaSeparatedStates)
