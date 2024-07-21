from simulator.test.fixtures import teams, effect_tracker, battle_map, test_battle_master_fighter_lvl_3


def test_combatant_ammo_reset(battle_map, teams, effect_tracker, test_battle_master_fighter_lvl_3):
    test_battle_master_fighter_lvl_3.ammo["Handaxe"].use_resource()
    assert test_battle_master_fighter_lvl_3.ammo["Handaxe"].get_resource() == 1
    test_battle_master_fighter_lvl_3.ammo["Handaxe"].use_resource()
    assert not test_battle_master_fighter_lvl_3.ammo["Handaxe"].has_resource()
    test_battle_master_fighter_lvl_3.ammo["Handaxe"].reset()
    assert test_battle_master_fighter_lvl_3.ammo["Handaxe"].get_resource() == 2
