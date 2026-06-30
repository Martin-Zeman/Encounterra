#include "core/feasibility.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "core/coords.hpp"
#include "actions/action_types.hpp"
#include "actions/movement.hpp"
#include "actions/smite_melee_attack.hpp"
#include "abilities/on_hit_divine_smite.hpp"
#include "effects/effect_tracker.hpp"

namespace enc
{

  namespace
  {
    bool isMovementAbility(AbilityType abilityType)
    {
      return abilityType > AbilityType::MOVEMENT_DELIMITER;
    }
  } // namespace

  bool checkFeasibility(Combatant *combatant, Actoid &actoid)
  {
    bool result = false;
    AbilityType abilityType = actoid.getAbilityType();
    if(abilityType == AbilityType::LAY_ON_HANDS || abilityType == AbilityType::DIVINE_SMITE)
      {
        result = combatant->hasBonusAction();
      }
    else if(abilityType > AbilityType::NOP && abilityType < AbilityType::BONUS_ACTION_DELIMITER)
      {
        result = combatant->hasAction();
      }
    else if(abilityType > AbilityType::BONUS_ACTION_DELIMITER && abilityType < AbilityType::REACTION_DELIMITER)
      {
        result = combatant->hasBonusAction();
      }
    else if(abilityType > AbilityType::REACTION_DELIMITER && abilityType < AbilityType::HASTE_ACTION_DELIMITER)
      {
        result = combatant->hasReaction();
      }
    else if(abilityType > AbilityType::HASTE_ACTION_DELIMITER && abilityType < AbilityType::PASSIVE_DELIMITER)
      {
        result = combatant->hasHasteAction();
      }
    else if(isMovementAbility(abilityType))
      {
        // Movement is gated by movement points (not the action/bonus/reaction/haste economy). Mirrors
        // Python check_feasibility's Movement branch.
        if(combatant->isAffectedByAny({Conditions::INCAPACITATED, Conditions::STUNNED, Conditions::PARALYZED}))
          {
            result = false;
          }
        else if(abilityType == AbilityType::GET_UP_FROM_PRONE)
          {
            result = combatant->getMovement() >= std::max(1, combatant->getSpeed() / 2);
          }
        else if(abilityType == AbilityType::STANDARD_MOVEMENT || abilityType == AbilityType::DISENGAGED_MOVEMENT)
          {
            auto &battleMap = BattleMap::getInstance();
            auto &movementIncrement = dynamic_cast<MovementIncrement &>(actoid);
            Coords targetPosition = battleMap.getCombatantCoordinates(*combatant) + movementIncrement.getIncrement();
            int movementNeeded = battleMap.isDifficultTerrainAt(targetPosition) ? 2 : 1;
            result = combatant->getMovement() >= movementNeeded && targetPosition.areValidCoords(battleMap.getGridSize()) &&
                     battleMap.areEmptyOrSelf(targetPosition, *combatant) &&
                     !combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::RESTRAINED});
          }
        else
          {
            result = false; // FORCED_MOVEMENT is not planned via getAction.
          }
        return result;
      }
    else if(abilityType == AbilityType::ACTION_SURGE)
      {
        // Free action: gated purely by its limited-use resource (checked in the switch below).
        result = true;
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
        // @todo: Add is reckless attack has been used
        // @todo: Check if they are enemies
        // @todo: Check range
        // @todo: Check if target is alive
        Attack &attack = dynamic_cast<Attack &>(actoid);
        // Multiattack: a second, complementary attack can be granted by the attack FSM even once the action
        // economy is spent (mirrors Python feasibility's `res |= not attack_fsm.is_0() and ...`).
        result = result || (!combatant->isAttackFsmAtStart() && combatant->attackFsmHasTransition(&attack.getFactory()));
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
      case AbilityType::SMITE_MELEE_ATTACK:
      {
        // A smite variant is a melee attack that also reserves the Bonus Action and a free cast / spell slot.
        Attack &attack = dynamic_cast<Attack &>(actoid);
        auto *smite = dynamic_cast<SmiteMeleeAttackFactory *>(&attack.getFactory());
        const ActoidFactory *base = smite ? smite->getBaseFactory() : &attack.getFactory();
        result = result || (!combatant->isAttackFsmAtStart() && combatant->attackFsmHasTransition(base));
        result &= combatant->hasBonusAction() && OnHitDivineSmite::canSmite(combatant);
        if(auto ammo = attack.getFactory().getResource())
          {
            result &= (*ammo)->hasUses();
          }
        break;
      }
      case AbilityType::FIREBALL:
      case AbilityType::HUNGER_OF_HADAR:
      case AbilityType::HYPNOTIC_PATTERN:
      case AbilityType::BLINK:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(combatant->getCastingSlotLevel(3));
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::SCORCHING_RAY:
      case AbilityType::HOLD_PERSON:
      case AbilityType::MISTY_STEP:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            // Misty Step can be cast from a level-2 slot or, with the Archfey Steps of the Fey invocation,
            // from a free limited-use pool (a plain Uses resource). The free version neither needs a slot nor
            // counts as casting a leveled spell this turn.
            if(actoid.getAbilityType() == AbilityType::MISTY_STEP && !dynamic_cast<Spellslots *>(*resource))
              {
                result &= (*resource)->hasUses();
                break;
              }
            result &= (*resource)->hasUses(combatant->getCastingSlotLevel(2));
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::QUICKENED_SCORCHING_RAY:
      case AbilityType::QUICKENED_HOLD_PERSON:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(2);
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        result &= combatant->getSorceryPoints() > 1;
        break;
      }
      case AbilityType::TWINNED_HOLD_PERSON:
      {
        // Twinned Spell (2024): costs 1 sorcery point to add a second target.
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(2);
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        result &= combatant->getSorceryPoints() > 0;
        break;
      }
      case AbilityType::QUICKENED_FIREBOLT:
      case AbilityType::QUICKENED_RAY_OF_FROST:
      {
        result &= combatant->getSorceryPoints() > 1;
        break;
      }
      case AbilityType::HEALING_WORD:
      case AbilityType::CURE_WOUNDS:
      case AbilityType::THUNDERWAVE:
      case AbilityType::FAERIE_FIRE:
      case AbilityType::BLESS:
      case AbilityType::GUIDING_BOLT:
      case AbilityType::SHIELD_OF_FAITH:
      case AbilityType::MAGIC_MISSILE:
      case AbilityType::MAGE_ARMOR:
      case AbilityType::SLEEP:
      case AbilityType::HEX:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(combatant->getCastingSlotLevel(1));
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::SPIKE_GROWTH:
      case AbilityType::FLAMING_SPHERE:
      case AbilityType::MOONBEAM:
      case AbilityType::DARKNESS:
      {
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(combatant->getCastingSlotLevel(2));
          }
        else
          {
            throw std::runtime_error("Actoid factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::INNATE_SORCERY:
      {
        // A bonus-action self-buff that lasts the encounter: never re-channel it while it is already active,
        // and only while uses remain.
        result &= !combatant->isInnateSorceryActive();
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses();
          }
        break;
      }
      case AbilityType::ARMOR_OF_AGATHYS:
      {
        // Level-1 bonus-action self-buff. Don't recast while the ward is still up; gated on a slot of the
        // caster's casting level (Warlocks upcast it to their pact-slot level) and the one-leveled-spell rule.
        result &= !EffectTracker::getInstance().isAffectingCombatant(combatant, EffectType::ARMOR_OF_AGATHYS);
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses(combatant->getCastingSlotLevel(1));
          }
        else
          {
            throw std::runtime_error("Armor of Agathys factory must have an associated resource!");
          }
        result &= !combatant->hasAlreadyUsedSpellslotThisTurn();
        break;
      }
      case AbilityType::FIREBOLT:
      case AbilityType::SACRED_FLAME:
      case AbilityType::TOLL_THE_DEAD:
      case AbilityType::ELDRITCH_BLAST:
      case AbilityType::ARMOR_OF_SHADOWS:
        /*Nothing to do*/
        break;

      case AbilityType::SECOND_WIND:
      case AbilityType::ACTION_SURGE:
      case AbilityType::RIPOSTE:
      case AbilityType::LAY_ON_HANDS:
      case AbilityType::VOW_OF_ENMITY:
      {
        // These class abilities are all gated by a flat
        // limited-use resource and consume no spell slot.
        if(auto resource = actoid.getFactory().getResource())
          {
            result &= (*resource)->hasUses();
          }
        else
          {
            throw std::runtime_error("Second Wind / Action Surge / Riposte factory must have an associated resource!");
          }
        break;
      }
      case AbilityType::DIVINE_SMITE:
      {
        result &= OnHitDivineSmite::canSmite(combatant);
        break;
      }

      default: break;
      }
    return result;
  }
  
}
