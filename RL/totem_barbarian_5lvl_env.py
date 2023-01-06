"""
Input should be concatenated states of K previous rounds. Both reset and step have to return those.

Encoding of Barbarian self:
[hp, has_action, has_bonus_action, has_reaction, x, y, [conditions affecting it], initiative(-4-40), attacks_left, num_rages, is_raging]
[1, 1, 1, 1, 1, 1, 15, 1, 1, 1, 1] -> 25

Encoding of the characters:
[#num, is_ally(0/1), health_condition(0-2), [conditions affecting it], x, y, size(0-5), initiative, has_action, has_bonus_action, has reaction]
[1, 1, 1, 15, 1, 1, 1, 1, 1, 1, 1] -> 25

Encoding of the map:
[[terrain_type(1-3)...terrain_type(1-3)], ..., [terrain_type(1-3)...terrain_type(1-3)]]
map_size ** 2


Encoding of actions Barbarian:
DONE
Movement.STANDARD, x_inc, y_inc
HasteAction.HASTE_DASH
HasteAction.HASTE_ATTACK char#
Action.ATTACK, char#
Action.DODGE
Action.DASH
FreeAction.RECKLESS_ATTACK
BonusAction.TOTEM_RAGE
==> Tuple(Discrete(?), Discrete(max(map_size_,num_characters)), Discrete(max(map_size_,num_characters)))
"""