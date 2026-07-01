#include "abilities/on_hit_divine_smite.hpp"

#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>
#include <iostream>

namespace enc
{
  Die OnHitDivineSmite::getDmgDice(int spellSlotLevel)
  {
    return Die{static_cast<unsigned char>(std::clamp(spellSlotLevel + 1, 2, 5)), 8};
  }

  Die OnHitDivineSmite::getDmgDiceUndeadOrFiend(int spellSlotLevel)
  {
    return Die{static_cast<unsigned char>(std::clamp(spellSlotLevel + 2, 3, 6)), 8};
  }

  bool OnHitDivineSmite::isUndeadOrFiend(Combatant *target)
  {
    Combatant *form = target->getOriginalForm();
    return form->isMonsterType(Monster::UNDEAD) || form->isMonsterType(Monster::FIEND);
  }

  bool OnHitDivineSmite::canSmite(Combatant *attacker)
  {
    if(attacker == nullptr || !attacker->hasPassiveAbility(AbilityType::DIVINE_SMITE))
      {
        return false;
      }
    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        return true;
      }
    if(attacker->hasAlreadyUsedSpellslotThisTurn())
      {
        return false;
      }
    for(int level = 4; level >= 1; --level)
      {
        if(attacker->getSpellslots().hasUses(level))
          {
            return true;
          }
      }
    return false;
  }

  int OnHitDivineSmite::chooseSmiteLevel(Combatant *attacker, Combatant *target, double multiplier, double dmgSoFar)
  {
    if(!canSmite(attacker))
      {
        return 0;
      }
    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        return 1;
      }

    for(int level = 4; level >= 1; --level)
      {
        if(attacker->getSpellslots().hasUses(level))
          {
            Die dice = isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(level) : getDmgDice(level);
            double avgDmg = avgRoll(dice);
            if((target->getCurrentHp() - dmgSoFar) * 1.3 >= avgDmg * multiplier)
              {
                return level;
              }
          }
      }
    return 0;
  }

  std::vector<std::pair<int, DamageType>>
  OnHitDivineSmite::hit(Combatant *attacker, Actoid * /*attack*/, Combatant *target, double multiplier, double dmgSoFar)
  {
    if(attacker == nullptr || target == nullptr)
      {
        return {};
      }

    int chosenLevel = chooseSmiteLevel(attacker, target, multiplier, dmgSoFar);
    if(chosenLevel == 0)
      {
        return {};
      }

    if(auto freeSmite = attacker->getResource(AbilityType::DIVINE_SMITE); freeSmite && (*freeSmite)->hasUses())
      {
        (*freeSmite)->useResource();
      }
    else
      {
        attacker->getSpellslots().useResource(chosenLevel);
        attacker->setAlreadyUsedSpellslotThisTurn(true);
      }

    Die dice = isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(chosenLevel) : getDmgDice(chosenLevel);
    int dmg = rollDice(dice);
    if(multiplier >= 2)
      {
        dmg *= 2;
      }
    std::cout << attacker->_name << " uses Divine Smite of level " << chosenLevel << " on " << target->_name << " for " << dmg
              << " Radiant damage" << std::endl;
    return {{dmg, DamageType::Radiant}};
  }

  double OnHitDivineSmite::calculateThreat(Combatant *attacker, Combatant *target, RollType rollType)
  {
    int chosenLevel = chooseSmiteLevel(attacker, target);
    if(chosenLevel == 0)
      {
        return 0.0;
      }
    return avgRoll(isUndeadOrFiend(target) ? getDmgDiceUndeadOrFiend(chosenLevel) : getDmgDice(chosenLevel));
  }
}
