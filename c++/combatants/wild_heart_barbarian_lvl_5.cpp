#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(int num)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, concatName(std::string(_className), num), 61, 15, 1, 0, 40,
                  15)
  {
    _instanceId = generateInstanceId();

    auto axe = addMeleeAttack("Two-handed axe", this,
                   7,                         // toHit
                   std::vector<Die>{{1, 12}}, // dmgDice
                   4,                         // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    addReactionAttack("Two-handed axe", this,
                      7,                         // toHit
                      std::vector<Die>{{1, 12}}, // dmgDice
                      4,                         // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );

    // Extra Attack (5th level): the barbarian makes two axe attacks per turn.
    addAttackTransition(axe.get(), AttackFsm::START, 1);
    addAttackTransition(axe.get(), 1, AttackFsm::NOP);
  }

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 61, 15, 1, 0, 40, 15)
  {
    _instanceId = generateInstanceId();

    auto axe = addMeleeAttack("Two-handed axe", this,
                   7,                         // toHit
                   std::vector<Die>{{1, 12}}, // dmgDice
                   4,                         // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    addReactionAttack("Two-handed axe", this,
                      7,                         // toHit
                      std::vector<Die>{{1, 12}}, // dmgDice
                      4,                         // dmgBonus
                      DamageType::Slashing,
                      1 // attackRange
    );

    // Extra Attack (5th level): the barbarian makes two axe attacks per turn.
    addAttackTransition(axe.get(), AttackFsm::START, 1);
    addAttackTransition(axe.get(), 1, AttackFsm::NOP);
  }
}
