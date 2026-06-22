#include "combatants/night_hag.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  NightHag::NightHag(int num)
      : Combatant(CombatantType::MONSTER, Monster::FIEND, _classLevel, concatName(std::string(_className), num), 112, 17, 2, 0, 30, 14,
                  {DamageType::Cold, DamageType::Fire}, {}, {}, Conditions::CHARMED)
  {
    _instanceId = generateInstanceId();

    auto claws = addMeleeAttack("Claws", this,
                   7,                        // toHit
                   std::vector<Die>{{2, 8}}, // dmgDice
                   4,                        // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    // addAbility(AbilityType::SPELLSLOTS, )

    // Single attack: the claws (no multiattack).
    addAttackTransition(claws.get(), AttackFsm::START, AttackFsm::NOP);
  }

  NightHag::NightHag(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::FIEND, _classLevel, name, 112, 17, 2, 0, 30, 14, {DamageType::Cold, DamageType::Fire}, {}, {},
                  Conditions::CHARMED)
  {
    _instanceId = generateInstanceId();

    auto claws = addMeleeAttack("Claws", this,
                   7,                        // toHit
                   std::vector<Die>{{2, 8}}, // dmgDice
                   4,                        // dmgBonus
                   DamageType::Slashing,
                   1 // attackRange
    );
    // addAbility(AbilityType::SPELLSLOTS, )

    // Single attack: the claws (no multiattack).
    addAttackTransition(claws.get(), AttackFsm::START, AttackFsm::NOP);
  }
}