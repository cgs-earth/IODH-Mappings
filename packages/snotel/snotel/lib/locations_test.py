from com.cache import RedisCache
from rise.lib.helpers import await_
from snotel.lib.types import StationDTO

def test_parse_locations():
    cache = RedisCache()
    result = await_(cache.get_or_fetch("https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?activeOnly=true"))
    locations = [StationDTO.model_validate(res) for res in result]
    assert locations 