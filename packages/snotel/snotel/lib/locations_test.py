from snotel.lib.locations import get_locations

def test_parse_locations():
    assert get_locations()

def test_filter_by_id():
    locations = get_locations()
    Zunir_R_ab_Black_Rock_Reservoir = "09386950"
    newCollection = locations.drop_all_locations_but_id(Zunir_R_ab_Black_Rock_Reservoir)
    assert len(newCollection.locations) == 1