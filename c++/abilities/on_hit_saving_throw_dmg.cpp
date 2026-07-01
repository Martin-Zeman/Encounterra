#include "abilities/on_hit_saving_throw_dmg.hpp"

#include <iostream>
#include "core/combatant.hpp"

namespace enc
{
  std::vector<std::pair<int, DamageType>>
  OnHitSavingThrowDmg::hit(Combatant *attacker, Actoid * /*attack*/, Combatant *target, double multiplier, double /*dmgSoFar*/)
  {
    int rolled = rollDiceMulti(_dmgDice);
    // A critical hit doubles the rider's damage dice, matching the base-attack crit multiplier.
    if(multiplier >= 2)
      {
        rolled *= 2;
      }

    bool saved = rollSavingThrow(target->getSavingThrow(_saveType), _dc, RollType::STRAIGHT);
    int dmg = rolled;
    if(saved)
      {
        dmg = _halfOnSuccess ? rolled / 2 : 0;
      }

    if(dmg <= 0)
      {
        return {};
      }

    std::cout << target->_name << (saved ? " resists part of" : " suffers") << " " << (_name.empty() ? "extra" : _name) << " damage ("
              << dmg << ")" << std::endl;
    return {{dmg, _dmgType}};
  }

  double OnHitSavingThrowDmg::calculateThreat(Combatant *attacker, Combatant *target, RollType rollType)
  {
    return meanDmgDcAttack(_dc, _dmgDice, _halfOnSuccess, target->getSavingThrow(_saveType), target->isImmuneTo(_dmgType),
                           target->isResistantTo(_dmgType));
  }
}
