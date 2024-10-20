#include "core/feasibility.hpp"
#include "core/combatant.hpp"
#include "actions/action_types.hpp"

namespace enc
{

  bool checkFeasibility(Combatant *combatant, Actoid &actoid)
  {
    bool result = false;
    AbilityType abilityType = actoid.getAbilityType();
    if(abilityType > AbilityType::NOP && abilityType < AbilityType::BONUS_ACTION_DELIMITER)
      {
        result = combatant->hasAction();
      }
    else if(abilityType > AbilityType::BONUS_ACTION_DELIMITER && abilityType < AbilityType::REACTION_DELIMITER)
      {
        result = combatant->hasBonusAction();
      }
    else if(abilityType > AbilityType::HASTE_ACTION_DELIMITER && abilityType < AbilityType::PASSIVE_DELIMITER)
      {
        result = combatant->hasHasteAction();
      }
    else
      {
        throw std::runtime_error("Unknown Ability Type in checkFeasibility!");
      }
    switch(actoid.getAbilityType())
      {
      case AbilityType::MELEE_ATTACK:
      case AbilityType::RANGED_ATTACK:
      case AbilityType::HASTE_MELEE_ATTACK:
      case AbilityType::HASTE_RANGED_ATTACK:
      case AbilityType::VAMPIRIC_BITE:
      case AbilityType::HASTE_VAMPIRIC_BITE:
      case AbilityType::PARALYZING_MELEE_ATTACK:
      case AbilityType::HASTE_PARALYZING_MELEE_ATTACK:
      {
        // @todo: Add FSM
        // @todo: Add is reckless attack has been used
        // @todo: Check if they are enemies
        // @todo: Check range
        // @todo: Check if target is alive
        Attack &attack = dynamic_cast<Attack &>(actoid);
        if(auto ammo = attack.getFactory().getResource())
          {
            result &= (*ammo)->hasUses();
          }
        else
          {
            throw std::runtime_error("Attack factory has no ammo!");
          }
        break;
      }
      case AbilityType::FIREBALL:
      case AbilityType::HUNGER_OF_HADAR:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(3);
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::FIREBOLT: /*Nothing to do*/ break;

      default: break;
      }
    return result;
  }

  bool checkFeasibilityLight(Combatant *combatant, Actoid &actoid)
  {
    bool result = false;
    AbilityType abilityType = actoid.getAbilityType();
    if(abilityType > AbilityType::NOP && abilityType < AbilityType::BONUS_ACTION_DELIMITER)
      {
        result = combatant->hasAction();
      }
    else if(abilityType > AbilityType::BONUS_ACTION_DELIMITER && abilityType < AbilityType::REACTION_DELIMITER)
      {
        result = combatant->hasBonusAction();
      }
    else if(abilityType > AbilityType::HASTE_ACTION_DELIMITER && abilityType < AbilityType::PASSIVE_DELIMITER)
      {
        result = combatant->hasHasteAction();
      }
    else
      {
        throw std::runtime_error("Unknown Ability Type in checkFeasibilityLight!");
      }
    switch(actoid.getAbilityType())
      {
      case AbilityType::MELEE_ATTACK:
      case AbilityType::RANGED_ATTACK:
      case AbilityType::HASTE_MELEE_ATTACK:
      case AbilityType::HASTE_RANGED_ATTACK:
      case AbilityType::VAMPIRIC_BITE:
      case AbilityType::HASTE_VAMPIRIC_BITE:
      case AbilityType::PARALYZING_MELEE_ATTACK:
      case AbilityType::HASTE_PARALYZING_MELEE_ATTACK:
      {
        // @todo: Add FSM
        // @todo: Add is reckless attack has been used
        Attack &attack = dynamic_cast<Attack &>(actoid);
        if(auto ammo = attack.getFactory().getResource())
          {
            result &= (*ammo)->hasUses();
          }
        else
          {
            throw std::runtime_error("Attack factory has no ammo!");
          }
        break;
      }
      case AbilityType::FIREBALL:
      case AbilityType::HUNGER_OF_HADAR:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(3);
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::FIREBOLT: /*Nothing to do*/ break;

      default: break;
      }
    return result;
  }
}
