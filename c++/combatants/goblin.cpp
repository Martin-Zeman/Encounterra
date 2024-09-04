#include "goblin.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Goblin::Goblin(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 7, 15, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    _size = Size::SMALL;

    addAbility<AbilityType::MELEE_ATTACK>("Scimitar",
                                          2,                                        // to_hit
                                          std::vector<std::pair<int, int>>{{1, 4}}, // damage dice
                                          0,                                        // damage bonus
                                          DamageType::Bludgeoning,
                                          1 // attack range
    );
  }
}