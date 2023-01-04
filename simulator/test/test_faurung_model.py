import pickle
import pytest

@pytest.fixture()
def inv_mapping():
    mapping = {'Firebolt': 0, 'Chaosbolt': 1, 'Haste': 2, 'Quickened Fireball': 3, 'Twinned Chaosbolt': 4,
               'Twinned Firebolt': 5,
               'Twinned Haste': 6, 'Fireball': 7}
    return {v: k for k, v in mapping.items()}
@pytest.fixture()
def model():
    with open('../decision_tree/faurung_model.pickle', 'rb') as handle:
        return pickle.load(handle)

def test_faurung_model(model, inv_mapping):
    # features = ['enemies', 'cast_leveled', 'ss1', 'ss2', 'ss3', 'enemy_adjacent', 'allies', 'is_concentrating', 'sorcery_points']
    assert inv_mapping[model.predict([[3, True, 4, 3, 2, False, 0, False, 0]])[0]] == "Firebolt"
    assert inv_mapping[model.predict([[4, False, 4, 3, 2, False, 0, False, 0]])[0]] == "Fireball"
    assert inv_mapping[model.predict([[4, False, 4, 3, 2, False, 0, False, 2]])[0]] == "Quickened Fireball"
    assert inv_mapping[model.predict([[3, False, 4, 3, 2, False, 0, False, 2]])[0]] == "Quickened Fireball"
    assert inv_mapping[model.predict([[3, False, 4, 3, 2, False, 0, False, 4]])[0]] == "Quickened Fireball"
    assert inv_mapping[model.predict([[2, False, 4, 3, 0, False, 0, False, 0]])[0]] == "Chaosbolt"
    assert inv_mapping[model.predict([[4, False, 4, 3, 0, False, 0, False, 0]])[0]] == "Chaosbolt"
    assert inv_mapping[model.predict([[4, False, 4, 3, 0, False, 0, False, 1]])[0]] == "Twinned Chaosbolt"
    assert inv_mapping[model.predict([[3, False, 4, 3, 0, False, 0, False, 1]])[0]] == "Twinned Chaosbolt"
    assert inv_mapping[model.predict([[2, False, 4, 3, 0, False, 0, False, 1]])[0]] == "Twinned Chaosbolt"
    assert inv_mapping[model.predict([[4, False, 0, 3, 0, False, 0, False, 0]])[0]] == "Firebolt"
    assert inv_mapping[model.predict([[4, False, 0, 0, 0, False, 0, False, 0]])[0]] == "Firebolt"
    assert inv_mapping[model.predict([[2, False, 0, 3, 0, False, 0, False, 1]])[0]] == "Twinned Firebolt"
    assert inv_mapping[model.predict([[2, False, 0, 0, 1, False, 1, False, 0]])[0]] == "Haste"
    assert inv_mapping[model.predict([[2, False, 0, 1, 1, False, 1, False, 0]])[0]] == "Haste"
    assert inv_mapping[model.predict([[2, False, 1, 1, 1, False, 1, False, 0]])[0]] == "Haste"
    assert inv_mapping[model.predict([[2, False, 1, 1, 1, False, 2, False, 0]])[0]] == "Haste"
    assert inv_mapping[model.predict([[2, False, 1, 1, 1, False, 2, True, 0]])[0]] == "Fireball"
    assert inv_mapping[model.predict([[1, False, 1, 1, 1, False, 2, True, 0]])[0]] == "Firebolt"
    assert inv_mapping[model.predict([[2, False, 1, 1, 1, False, 2, False, 3]])[0]] == "Twinned Haste"