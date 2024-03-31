from simulator.eligible_coords import EligibleCoordinates, LocationIndependent


def test_eligible_locations_contains():
    coords = [(1, 2), (3, 4)]
    eligible_locations = EligibleCoordinates(coordinates=coords)
    assert (1, 2) in eligible_locations
    assert (5, 6) not in eligible_locations


def test_eligible_locations_iter_and_len():
    coords = [(1, 2), (3, 4), (5, 6)]
    eligible_locations = EligibleCoordinates(coordinates=coords)
    assert len(eligible_locations) == 3
    assert list(iter(eligible_locations)) == coords


def test_eligible_locations_bool():
    coords = [(1, 2)]
    no_coords = []
    assert EligibleCoordinates(coordinates=coords)
    assert not EligibleCoordinates(coordinates=no_coords)


def test_location_independent_contains():
    location_independent = LocationIndependent()
    assert (1, 2) in location_independent
    assert (100, 200) in location_independent


def test_location_independent_iter_and_len():
    location_independent = LocationIndependent()
    assert len(location_independent) == 0
    assert list(iter(location_independent)) == []


def test_location_independent_bool():
    location_independent = LocationIndependent()
    assert location_independent
