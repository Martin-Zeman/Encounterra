from itertools import product
import pandas as pd


if __name__ == '__main__':
    enemies = [1, 2, 3, 4]
    cast_leveled = [True, False]
    ss1 = [0, 1, 2, 3, 4]
    ss2 = [0, 1, 2, 3]
    ss3 = [0, 1, 2]
    enemy_adjacent = [True, False]
    allies = [0, 1, 2]
    is_concentrating = [True, False]
    sorcery_points = [0, 1, 2, 3, 4, 5]
    comb = pd.DataFrame(list(product(enemies, cast_leveled, ss1, ss2, ss3, enemy_adjacent, allies, is_concentrating, sorcery_points)), columns=['enemies', 'cast_leveled', 'ss1', 'ss2', 'ss3', 'enemy_adjacent', 'allies', 'is_concentrating', 'sorcery_points'])
    comb['decision'] = "Firebolt"
    comb.loc[(comb['cast_leveled'] is False) & (comb['ss3'] == 0) & (comb['ss1'] > 0), ['decision']] = 'Chaosbolt'
    comb.loc[(comb['cast_leveled'] is False) & (comb['enemies'] > 1) & (comb['ss3'] > 0), ['decision']] = 'Fireball'
    comb.loc[(comb['cast_leveled'] is False) & (comb['allies'] > 0) & (comb['is_concentrating'] is False) & (comb['ss3'] > 0), ['decision']] = 'Haste'

    comb.loc[(comb['cast_leveled'] is False) & (comb['enemies'] > 2) & (comb['ss3'] > 0) & (comb['sorcery_points'] > 1), ['decision']] = 'Quickened Fireball'
    comb.loc[(comb['cast_leveled'] is False) & ((comb['ss3'] == 0) | (comb['enemies'] < 2)) & (comb['ss1'] > 0) & (comb['sorcery_points'] > 0) & (comb['enemies'] > 1), ['decision']] = 'Twinned Chaosbolt'
    comb.loc[(comb['cast_leveled'] is False) & (comb['ss1'] == 0) & (comb['sorcery_points'] > 0) & (comb['enemies'] > 1), ['decision']] = 'Twinned Firebolt'
    comb.loc[(comb['cast_leveled'] is False) & (comb['allies'] > 1) & (comb['is_concentrating'] is False) & (comb['ss3'] > 0) & (comb['sorcery_points'] > 2), ['decision']] = 'Twinned Haste'

    comb.to_csv('faurung_table.csv')
