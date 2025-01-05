#include "acolyte.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Acolyte::Acolyte(int num) : Acolyte(concatName(std::string(_className), num)) {}

  Acolyte::Acolyte(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 9, 10, 0, 4, 30, 12)
  {
    _instanceId = generateInstanceId();

    addMeleeAttack("Club", this,
                   2,                        // toHit
                   std::vector<Die>{{1, 4}}, // dmgDice
                   0,                        // dmgBonus
                   DamageType::Bludgeoning,
                   1 // attackRange
    );
    addSpellSlots(CombatantType::CLERIC, 2);
  }

  ResourceState Acolyte::exportResources()
  {
    // TODO
    return {};
  }
  void Acolyte::importResources(const ResourceState &resources)
  {
    // TODO
  }
}