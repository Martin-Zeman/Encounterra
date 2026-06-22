#include "acolyte.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  Acolyte::Acolyte(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 9, 10, 0, 4, 30, 12)
  {
    _instanceId = generateInstanceId();

    auto club = addMeleeAttack("Club", this,
                   2,                        // toHit
                   std::vector<Die>{{1, 4}}, // dmgDice
                   0,                        // dmgBonus
                   DamageType::Bludgeoning,
                   1 // attackRange
    );
    addSpellSlots(CombatantType::CLERIC, 2);

    // Single attack: the club (no multiattack).
    addAttackTransition(club.get(), AttackFsm::START, AttackFsm::NOP);
  }

  Acolyte::Acolyte(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 9, 10, 0, 4, 30, 12)
  {
    _instanceId = generateInstanceId();

    auto club = addMeleeAttack("Club", this,
                   2,                        // toHit
                   std::vector<Die>{{1, 4}}, // dmgDice
                   0,                        // dmgBonus
                   DamageType::Bludgeoning,
                   1 // attackRange
    );
    addSpellSlots(CombatantType::CLERIC, 2);

    // Single attack: the club (no multiattack).
    addAttackTransition(club.get(), AttackFsm::START, AttackFsm::NOP);
  }
}