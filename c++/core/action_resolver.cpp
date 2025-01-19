#include "action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/types.hpp"
#include "core/feasibility.hpp"
#include "actions/dodge.hpp"

namespace enc
{
  bool hasAdvantageSavingThrow(SavingThrow savingThrow, const Combatant &target, bool isSpellEffect)
  {
    if((target.getSavingThrowRollTypeMods(savingThrow) & RollType::ADVANTAGE) == RollType::ADVANTAGE)
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target.hasPassiveAbility(AbilityType::DANGER_SENSE)
       && !target.isAffectedByAny({Conditions::INCAPACITATED, Conditions::BLINDED, Conditions::DEAFENED}))
      {
        std::cout << target._name << " gains advantage through Danger Sense" << std::endl;
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target.isDodging())
      {
        std::cout << target._name << " gains advantage by dodging" << std::endl;
        return true;
      }

    if(isSpellEffect && target.hasPassiveAbility(AbilityType::MAGIC_RESISTANCE))
      {
        std::cout << target._name << " gains advantage through Magic Resistance" << std::endl;
        return true;
      }

    return false;
  }

  bool hasDisadvantageSavingThrow(SavingThrow savingThrow, const Combatant &target)
  {
    if((target.getSavingThrowRollTypeMods(savingThrow) & RollType::DISADVANTAGE) == RollType::DISADVANTAGE)
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target.isAffectedByAny({Conditions::RESTRAINED}))
      {
        std::cout << target._name << " is restrained" << std::endl;
        return true;
      }

    return false;
  }

  void resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant &target,
                             bool halfOnSuccess, bool isSpellEffect)
  {
    auto stBonus = target.getSavingThrow(savingThrowType);

    // Determine advantage/disadvantage
    RollType types;
    if(hasAdvantageSavingThrow(savingThrowType, target, isSpellEffect))
      {
        types |= RollType::ADVANTAGE;
      }
    if(hasDisadvantageSavingThrow(savingThrowType, target))
      {
        types |= RollType::DISADVANTAGE;
      }
    auto finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;

    if(finalModifier == RollType::STRAIGHT)
      {
        rolled = rollDice(d20);
      }
    else if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else
      { // DISADVANTAGE
        rolled = std::min(rollDice(d20), rollDice(d20));
      }

    // Handle natural 1s and 20s
    bool saved;
    if(rolled == 1)
      {
        saved = false;
      }
    else if(rolled == 20)
      {
        saved = true;
      }
    else
      {
        // Add bonus dice modifiers
        for(const auto &bonusDie : target.getSavingThrowDiceMods(savingThrowType))
          {
            int bonusDiceRoll = rollDice(bonusDie);
            std::cout << "Adding " << bonusDiceRoll << " from bonus " << bonusDie << "to the roll" << std::endl;
            rolled += bonusDiceRoll;
          }
        saved = (rolled + stBonus >= dc);
      }

    // Apply damage
    if(!saved)
      {
        if(savingThrowType == SavingThrow::DEX && target.hasPassiveAbility(AbilityType::EVASION))
          {
            dmg /= 2;
            std::cout << target._name << " failed the save but only receives " << dmg << " damage thanks to Evasion" << std::endl;
          }
        else
          {
            std::cout << abilityName << " deals " << dmg << " to " << target._name << std::endl;
            target.receiveDmg(dmg, dmgType);
          }
      }
    else if(halfOnSuccess)
      {
        if(savingThrowType == SavingThrow::DEX && target.hasPassiveAbility(AbilityType::EVASION))
          {
            std::cout << target._name << " made the save and receives no damage thanks to Evasion" << std::endl;
          }
        else
          {
            dmg /= 2;
            std::cout << abilityName << " deals " << dmg << " to " << target._name << std::endl;
            target.receiveDmg(dmg, dmgType);
          }
      }

    BattleMap::getInstance().removeCombatantIfDead(target);
  }

  ActionResult resolveByActoidFlags(const std::shared_ptr<Actoid> &action, Combatant &combatant)
  {
    // TODO:
    return ActionResult::MISS;
  }

  std::shared_ptr<Actoid> handleErrorCase(const std::shared_ptr<Actoid> &action, Combatant &combatant)
  {
    if(action->getFactory().getAbilityType() == AbilityType::STANDARD_MOVEMENT)
      {
        std::cerr << combatant._name << " doesn't have enough movement to enter difficult terrain" << std::endl;
        combatant.setMovement(0); // This can be caused by difficult terrain which is ok, but we must avoid endless looping
        return nullptr;
      }

    if(combatant.hasAction())
      {
        std::cerr << "Action " << action->toString() << " by " << combatant._name << " is not feasible. Taking the Dodge action!" << std::endl;
        auto dodgeFactory = std::make_shared<DodgeFactory>(combatant);
        return dodgeFactory->create({});
      }

    std::cerr << "Action " << action->toString() << " by " << combatant._name << " is not feasible" << std::endl;
    return nullptr;
  }

  ActionResult resolveAction(const std::shared_ptr<Actoid> &action, Combatant &combatant)
  {
    // Takes care of possible wildshape
    auto currentForm = combatant.getCurrentForm().lock();

    if(!action)
      {
        return ActionResult::UNFEASIBLE;
      }

    if(!checkFeasibility(*currentForm, *action))
      {
        auto newAction = handleErrorCase(action, *currentForm);
        if(!newAction)
          {
            return ActionResult::UNFEASIBLE;
          }
        useResources(*currentForm, *newAction);
        return resolveByActoidFlags(newAction, *currentForm);
      }

    useResources(*currentForm, *action);
    return resolveByActoidFlags(action, *currentForm);
  }

  void resolveEffects(const std::vector<std::weak_ptr<Effect>> &effects, Combatant &combatant)
  {
    for(const auto &weakEffect : effects)
      {
        if(auto effect = weakEffect.lock())
          {
            EffectType effectType = effect->getEffectType();

            switch(effectType)
              {
              case EffectType::HASTE:
              case EffectType::TWINNED_HASTE:
                combatant.setMovement(combatant.getSpeed() * 2);
                combatant.setHasHasteAction(true);
                break;

              case EffectType::POST_HASTE_LETHARGY:
                combatant.setMovement(0);
                combatant.setHasAction(false);
                combatant.setHasBonusAction(false);
                combatant.setHasReaction(false);
                break;

              case EffectType::RAGE:
              case EffectType::TOTEM_RAGE:
              case EffectType::WILDSHAPE:
              case EffectType::DODGE:
              case EffectType::DISENGAGE:
              case EffectType::RECKLESS_ATTACK:
              case EffectType::FLAMING_SPHERE:
              case EffectType::SPIKE_GROWTH:
              case EffectType::CLOUD_OF_DAGGERS:
              case EffectType::HUNGER_OF_HADAR:
              case EffectType::FAERIE_FIRE:
              case EffectType::HOLD_PERSON:
              case EffectType::DIGESTION:
              case EffectType::BLESS:
              case EffectType::REGENERATION:
              case EffectType::SLEEP:
              case EffectType::SHIELD_OF_FAITH:
              case EffectType::SHILLELAGH:
              case EffectType::MENACING_ATTACK_FRIGHTENED:
              case EffectType::VOW_OF_ENMITY:
              case EffectType::RAY_OF_FROST:
              case EffectType::PARALYZING_ATTACK_PARALYZED:
                // TODO: track if the barbarian attacked or received damage
                break;

              default: std::cerr << "Unknown effect " << static_cast<int>(effectType) << std::endl; break;
              }
          }
      }
  }
} // namespace enc
