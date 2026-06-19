#include "abilities/on_hit_grapple.hpp"

#include <iostream>
#include "core/combatant.hpp"

namespace enc
{
  std::vector<std::pair<int, DamageType>>
  OnHitGrapple::hit(Combatant *attacker, Actoid * /*attack*/, Combatant *target, double /*multiplier*/, double /*dmgSoFar*/)
  {
    // 2024: a creature can be grappled by only one grappler (per body part). If something already
    // grapples the target, do not overwrite that grapple.
    if (target->getInitiatorOfCondition(Conditions::GRAPPLED) != nullptr)
    {
      return {};
    }

    // Athletics is a Strength skill, Acrobatics a Dexterity skill. ConditionWithDC stores a
    // SavingThrow; the escape check itself uses max(Athletics, Acrobatics) regardless, so this is
    // only bookkeeping for the associated ability.
    SavingThrow associated = (_escapeSkill == SkillCheck::ACROBATICS) ? SavingThrow::DEX : SavingThrow::STR;

    std::cout << attacker->_name << " grapples " << target->_name << " (escape DC " << _dc << ")" << std::endl;
    target->applyDCCondition(ConditionWithDC(Conditions::GRAPPLED, associated, _dc, attacker, PhaseOfTurn::ACTION));
    attacker->applyCondition(Condition(Conditions::GRAPPLING, attacker, nullptr, target));
    return {};
  }
}
