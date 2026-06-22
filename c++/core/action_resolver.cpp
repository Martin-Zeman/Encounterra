#include "action_resolver.hpp"
#include "core/battle_map.hpp"
#include "core/types.hpp"
#include "core/feasibility.hpp"
#include "actions/dodge.hpp"
#include "actions/attack.hpp"
#include "actions/break_grapple.hpp"
#include "actions/movement.hpp"
#include "spells/firebolt.hpp"
#include "spells/ray_of_frost.hpp"
#include "spells/scorching_ray.hpp"
#include "spells/misty_step.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{
  bool hasAdvantageSavingThrow(SavingThrow savingThrow, Combatant *target, bool isSpellEffect)
  {
    if(target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::ADVANTAGE))
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::DANGER_SENSE)
       && !target->isAffectedByAny({Conditions::INCAPACITATED, Conditions::BLINDED, Conditions::DEAFENED}))
      {
        std::cout << target->_name << " gains advantage through Danger Sense" << std::endl;
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->isDodging())
      {
        std::cout << target->_name << " gains advantage by dodging" << std::endl;
        return true;
      }

    if(isSpellEffect && target->hasPassiveAbility(AbilityType::MAGIC_RESISTANCE))
      {
        std::cout << target->_name << " gains advantage through Magic Resistance" << std::endl;
        return true;
      }

    return false;
  }

  bool hasDisadvantageSavingThrow(SavingThrow savingThrow, Combatant *target)
  {
    if(target->getSavingThrowRollTypeMods(savingThrow).contains(RollType::DISADVANTAGE))
      {
        return true;
      }

    if(savingThrow == SavingThrow::DEX && target->isAffectedByAny({Conditions::RESTRAINED}))
      {
        std::cout << target->_name << " is restrained" << std::endl;
        return true;
      }

    return false;
  }

  void resolveDmgSavingThrow(SavingThrow savingThrowType, int dc, const std::string &abilityName, int dmg, DamageType dmgType, Combatant *target,
                             bool halfOnSuccess, bool isSpellEffect)
  {
    auto stBonus = target->getSavingThrow(savingThrowType);

    // Determine advantage/disadvantage
    std::unordered_set<RollType> types;
    if(hasAdvantageSavingThrow(savingThrowType, target, isSpellEffect))
      {
        types.insert(RollType::ADVANTAGE);
      }
    if(hasDisadvantageSavingThrow(savingThrowType, target))
      {
        types.insert(RollType::DISADVANTAGE);
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
        for(const auto &bonusDie : target->getSavingThrowDiceMods(savingThrowType))
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
        if(savingThrowType == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::EVASION))
          {
            dmg /= 2;
            std::cout << target->_name << " failed the save but only receives " << dmg << " damage thanks to Evasion" << std::endl;
          }
        else
          {
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
          }
      }
    else if(halfOnSuccess)
      {
        if(savingThrowType == SavingThrow::DEX && target->hasPassiveAbility(AbilityType::EVASION))
          {
            std::cout << target->_name << " made the save and receives no damage thanks to Evasion" << std::endl;
          }
        else
          {
            dmg /= 2;
            std::cout << abilityName << " deals " << dmg << " to " << target->_name << std::endl;
            target->receiveDmg(dmg, dmgType);
          }
      }

    BattleMap::getInstance().removeCombatantIfDead(*target);
  }

  std::shared_ptr<Actoid> ActionResolver::handleErrorCase(const std::shared_ptr<Actoid> &action, Combatant *combatant)
  {
    if(action->getFactory().getAbilityType() == AbilityType::STANDARD_MOVEMENT)
      {
        std::cerr << combatant->_name << " doesn't have enough movement to enter difficult terrain" << std::endl;
        combatant->setMovement(0); // This can be caused by difficult terrain which is ok, but we must avoid endless looping
        return nullptr;
      }

    if(combatant->hasAction())
      {
        std::cerr << "Action " << action->toString() << " by " << combatant->_name << " is not feasible. Taking the Dodge action!" << std::endl;
        auto dodgeFactory = std::make_shared<DodgeFactory>(combatant);
        return dodgeFactory->create({});
      }

    std::cerr << "Action " << action->toString() << " by " << combatant->_name << " is not feasible" << std::endl;
    return nullptr;
  }

  ActionResult ActionResolver::resolveAttack(Attack *attack, Combatant *target, Combatant *attacker)
  {
    auto &battleMap = BattleMap::getInstance();
    AttackFactory &factory = attack->getAttackFactory();

    // Minimal port of resolve_attack: evaluate the grapple-related advantage/disadvantage sources.
    std::unordered_set<RollType> types;
    // 2024: a Grappled creature has Disadvantage on attack rolls against any target other than the grappler.
    if(attacker->isAffectedBy(Conditions::GRAPPLED) && attacker->getInitiatorOfCondition(Conditions::GRAPPLED) != target)
      {
        types.insert(RollType::DISADVANTAGE);
      }
    // Some attacks (e.g. the Bugbear Warrior's Light Hammer) have Advantage against a creature this combatant grapples.
    if(factory.hasAdvantageVsGrappledTarget() && target->getInitiatorOfCondition(Conditions::GRAPPLED) == attacker)
      {
        types.insert(RollType::ADVANTAGE);
      }
    RollType finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;
    if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else if(finalModifier == RollType::DISADVANTAGE)
      {
        rolled = std::min(rollDice(d20), rollDice(d20));
      }
    else
      {
        rolled = rollDice(d20);
      }

    std::cout << attacker->_name << " attacks " << target->_name << " with " << factory._name << std::endl;

    int multiplier = 1;
    if(rolled == 1)
      {
        std::cout << "Natural 1 rolled!" << std::endl;
        return ActionResult::MISS;
      }
    else if(rolled >= 21 - factory.getCritRange())
      {
        multiplier = 2;
      }

    if(rolled + factory.getToHit() >= target->getAC())
      {
        int dmgDiceSum = rollDiceMulti(factory.getDmgDice());
        int baseDmg = multiplier * dmgDiceSum + factory.getDmgBonus();
        if(baseDmg < 0)
          {
            baseDmg = 0;
          }
        std::cout << "The attack " << (multiplier == 2 ? "CRITS" : "hits") << " " << target->_name << " for " << baseDmg << " damage"
                  << std::endl;
        std::vector<std::pair<int, DamageType>> compoundDmg = {{baseDmg, factory.getDmgType()}};
        attack->setRollType(finalModifier);
        target->receiveCompoundDmg(compoundDmg, multiplier);
        battleMap.removeCombatantIfDead(*target);
        // Apply on-hit riders (e.g. the grapple from a Grab) while the target is still in play.
        if(target->isAlive())
          {
            for(const auto &onHit : factory.getOnHits())
              {
                auto extraDmg = onHit->hit(attacker, attack, target, multiplier, baseDmg);
                if(!extraDmg.empty())
                  {
                    target->receiveCompoundDmg(extraDmg, multiplier);
                    battleMap.removeCombatantIfDead(*target);
                  }
              }
          }
        return ActionResult::HIT;
      }

    std::cout << "The attack misses " << target->_name << std::endl;
    return ActionResult::MISS;
  }

  ActionResult ActionResolver::resolveRangedSpellAttack(Combatant *caster, int toHit, const Die &dmgDice, DamageType dmgType, Combatant *target)
  {
    auto &battleMap = BattleMap::getInstance();

    // Minimal port of resolve_ranged_spell_attack: collect the relevant advantage/disadvantage sources.
    std::unordered_set<RollType> types;
    // Innate Sorcery grants the caster advantage on its own spell attack rolls.
    if(caster->isInnateSorceryActive())
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Attacking a Paralyzed/Restrained/Stunned/Blinded creature is made with advantage.
    if(target->isAffectedByAny({Conditions::PARALYZED, Conditions::RESTRAINED, Conditions::STUNNED, Conditions::BLINDED}))
      {
        types.insert(RollType::ADVANTAGE);
      }
    // Ranged spell attacks are made with disadvantage while an enemy is adjacent to the caster.
    if(battleMap.isEnemyAdjacent(*caster))
      {
        types.insert(RollType::DISADVANTAGE);
      }
    if(target->isDodging())
      {
        types.insert(RollType::DISADVANTAGE);
      }
    RollType finalModifier = reconcileRollTypes(types);

    Die d20{1, 20};
    int rolled;
    if(finalModifier == RollType::ADVANTAGE)
      {
        rolled = std::max(rollDice(d20), rollDice(d20));
      }
    else if(finalModifier == RollType::DISADVANTAGE)
      {
        rolled = std::min(rollDice(d20), rollDice(d20));
      }
    else
      {
        rolled = rollDice(d20);
      }

    std::cout << caster->_name << " rolls a spell attack against " << target->_name << std::endl;

    if(rolled == 1)
      {
        std::cout << "Natural 1 rolled!" << std::endl;
        return ActionResult::MISS;
      }
    int multiplier = (rolled == 20) ? 2 : 1;

    if(rolled + toHit >= target->getAC())
      {
        int dmg = multiplier * rollDiceMulti({dmgDice});
        if(dmg < 0)
          {
            dmg = 0;
          }
        std::cout << "The spell " << (multiplier == 2 ? "CRITS" : "hits") << " " << target->_name << " for " << dmg << " damage" << std::endl;
        target->receiveDmg(dmg, dmgType, multiplier);
        battleMap.removeCombatantIfDead(*target);
        return ActionResult::HIT;
      }

    std::cout << "The spell misses " << target->_name << std::endl;
    return ActionResult::MISS;
  }

  bool ActionResolver::requestMovement(Combatant *movingCombatant, MovementIncrement *movement)
  {
    auto &battleMap = BattleMap::getInstance();

    if(movement->incursAOO())
      {
        auto aooCandidates = battleMap.getAooEligibleCombatants(movingCombatant, movement->getIncrement());
        for(auto *candidate : aooCandidates)
          {
            AttackFactory *aooFactory = candidate->getAoOFactory();
            if(aooFactory && candidate->hasReaction() && movingCombatant->isAlive())
              {
                // The reaction is consumed inside resolveAction -> useResources (mirrors Python prompt_aoo,
                // which leaves has_reaction for use_resources to clear). checkFeasibility still sees the
                // reaction as available.
                auto aoo = aooFactory->create(movingCombatant);
                resolveAction(aoo, candidate);
              }
          }
      }

    if(movingCombatant->isAlive())
      {
        battleMap.moveCombatantByIncrement(*movingCombatant, movement->getIncrement());
        return true;
      }
    return false;
  }

  ActionResult ActionResolver::resolveByActoidFlags(const std::shared_ptr<Actoid> &action, Combatant *combatant)
  {
    switch(action->getAbilityType())
      {
      case AbilityType::MELEE_ATTACK:
      case AbilityType::RANGED_ATTACK:
      case AbilityType::BONUS_MELEE_ATTACK:
      case AbilityType::BONUS_RANGED_ATTACK:
      case AbilityType::HASTE_MELEE_ATTACK:
      case AbilityType::HASTE_RANGED_ATTACK:
      case AbilityType::REACTION_ATTACK:
        {
          auto *attack = dynamic_cast<Attack *>(action.get());
          if(!attack)
            {
              return ActionResult::MISS;
            }
          return resolveAttack(attack, &attack->getTarget(), combatant);
        }

      case AbilityType::STANDARD_MOVEMENT:
      case AbilityType::DISENGAGED_MOVEMENT:
        {
          // 2024: the Grappled (and Restrained) condition sets Speed to 0, so movement is blocked.
          if(combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::RESTRAINED}))
            {
              std::cout << combatant->_name << " can't move (Speed 0 while grappled/restrained)" << std::endl;
              return ActionResult::OTHER;
            }
          auto *movement = dynamic_cast<MovementIncrement *>(action.get());
          if(!movement)
            {
              return ActionResult::MISS;
            }
          if(!requestMovement(combatant, movement))
            {
              return ActionResult::MISS;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::BREAK_GRAPPLE:
        {
          auto *breakGrappleFactory = dynamic_cast<BreakGrappleFactory *>(&action->getFactory());
          if(!breakGrappleFactory)
            {
              return ActionResult::MISS;
            }
          const ConditionWithDC &grapple = breakGrappleFactory->getGrappleCondition();
          // 2024 escape: the Grappled creature uses its action for a Strength (Athletics) or
          // Dexterity (Acrobatics) check against the escape DC, ending the condition on a success.
          int bonus = std::max(combatant->getAthletics(), combatant->getAcrobatics());
          std::cout << combatant->_name << " attempts to escape the grapple (DC " << grapple.dc << ")" << std::endl;
          if(rollAbilityCheck(bonus, grapple.dc, RollType::STRAIGHT))
            {
              std::cout << combatant->_name << " breaks free of the grapple" << std::endl;
              if(grapple.initiator != nullptr)
                {
                  grapple.initiator->removeCondition(Conditions::GRAPPLING);
                }
              combatant->breakOutOfGrapple();
            }
          else
            {
              std::cout << combatant->_name << " fails to escape the grapple" << std::endl;
            }
          return ActionResult::OTHER;
        }

      case AbilityType::DODGE:
      case AbilityType::DISENGAGE:
        // Minimal: the defensive effect is not applied yet, but the action is consumed by the planner.
        std::cout << combatant->_name << " takes the " << action->toString() << " action" << std::endl;
        return ActionResult::OTHER;

      case AbilityType::FIREBOLT:
      case AbilityType::QUICKENED_FIREBOLT:
        {
          auto *firebolt = dynamic_cast<Firebolt *>(action.get());
          if(!firebolt)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          return resolveRangedSpellAttack(combatant, firebolt->getToHit(), firebolt->getDmgDice(), FireboltFactory::dmgType, &firebolt->getTarget());
        }

      case AbilityType::RAY_OF_FROST:
      case AbilityType::QUICKENED_RAY_OF_FROST:
        {
          auto *rayOfFrost = dynamic_cast<RayOfFrost *>(action.get());
          if(!rayOfFrost)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // The 2024 Speed-reduction rider is not modeled (see RayOfFrostFactory); only the damage resolves.
          return resolveRangedSpellAttack(combatant, rayOfFrost->getToHit(), rayOfFrost->getDmgDice(), RayOfFrostFactory::dmgType,
                                          &rayOfFrost->getTarget());
        }

      case AbilityType::SCORCHING_RAY:
      case AbilityType::QUICKENED_SCORCHING_RAY:
        {
          auto *scorchingRay = dynamic_cast<ScorchingRay *>(action.get());
          if(!scorchingRay)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          // All rays are concentrated on the single chosen target (matching the threat model); each is a
          // separate spell attack and stops early if the target dies.
          Combatant *target = &scorchingRay->getTarget();
          ActionResult result = ActionResult::MISS;
          for(int ray = 0; ray < ScorchingRay::getNumRays() && target->isAlive(); ++ray)
            {
              ActionResult rayResult =
                  resolveRangedSpellAttack(combatant, scorchingRay->getToHit(), scorchingRay->getDmgDice(), ScorchingRayFactory::dmgType, target);
              if(rayResult == ActionResult::HIT)
                {
                  result = ActionResult::HIT;
                }
            }
          return result;
        }

      case AbilityType::HOLD_PERSON:
      case AbilityType::QUICKENED_HOLD_PERSON:
        {
          auto effect = std::dynamic_pointer_cast<Effect>(action);
          if(!effect)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          EffectTracker::getInstance().add(effect);
          effect->activate();
          return ActionResult::OTHER;
        }

      case AbilityType::MISTY_STEP:
        {
          auto *mistyStep = dynamic_cast<MistyStep *>(action.get());
          if(!mistyStep)
            {
              return ActionResult::MISS;
            }
          std::cout << combatant->_name << " casts " << action->toString() << std::endl;
          BattleMap::getInstance().moveCombatant(*combatant, mistyStep->getCoord());
          return ActionResult::OTHER;
        }

      case AbilityType::SHIELD:
        // Reaction: +5 AC until the start of the caster's next turn.
        std::cout << combatant->_name << " casts Shield" << std::endl;
        combatant->applyShieldSpell();
        return ActionResult::OTHER;

      case AbilityType::INNATE_SORCERY:
        // Bonus action self-buff: grants advantage on the caster's spell attacks for the encounter.
        std::cout << combatant->_name << " channels Innate Sorcery" << std::endl;
        combatant->setInnateSorceryActive(true);
        return ActionResult::OTHER;

      default:
        std::cerr << "resolveByActoidFlags: unhandled action " << action->toString() << " (treating as no-op)" << std::endl;
        return ActionResult::OTHER;
      }
  }

ActionResult ActionResolver::resolveAction(const std::shared_ptr<Actoid>& action, Combatant* combatant) 
{
    // Takes care of possible wildshape
    combatant = combatant->getCurrentForm();

    if (!action) {
        return ActionResult::UNFEASIBLE;
    }

    if (!checkFeasibility(combatant, *action)) {
        auto newAction = handleErrorCase(action, combatant);
        if (!newAction) {
            return ActionResult::UNFEASIBLE;
        }
        useResources(combatant, *newAction);
        return resolveByActoidFlags(newAction, combatant);
    }

    useResources(combatant, *action);
    return resolveByActoidFlags(action, combatant);
}

  void ActionResolver::resolveEffects(const std::unordered_set<std::shared_ptr<Effect>> &effects, Combatant *combatant)
  {
    for(const auto &effect : effects)
      {
        EffectType effectType = effect->getEffectType();

        switch(effectType)
          {
          case EffectType::HASTE:
          case EffectType::TWINNED_HASTE:
            combatant->setMovement(combatant->getSpeed() * 2);
            combatant->setHasHasteAction(true);
            break;

          case EffectType::POST_HASTE_LETHARGY:
            combatant->setMovement(0);
            combatant->setHasAction(false);
            combatant->setHasBonusAction(false);
            combatant->setHasReaction(false);
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
  } // namespace enc
