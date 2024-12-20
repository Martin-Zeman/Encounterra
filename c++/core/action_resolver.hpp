#pragma once

#include "core/interfaces.hpp"
#include "core/combatant.hpp"

namespace enc
{
  class ActionResolver
  {
    // TODO
    bool hasAdvantageSavingThrow(SavingThrow savingThrow, Combatant *target, bool isSpellEffect);
    bool hasDisadvantageSavingThrow(SavingThrow savingThrow, Combatant *target);
    void resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant *target,
                               bool halfOnSuccess = false, bool isSpellEffect = false)
  };
}