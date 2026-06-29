#include "core/resources.hpp"
#include "core/interfaces.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "actions/action_types.hpp"
#include "actions/movement.hpp"
#include "actions/smite_melee_attack.hpp"
#include "abilities/lay_on_hands.hpp"
#include <algorithm>

namespace enc
{

  void useResources(Combatant *combatant, Actoid &actoid)
  {
    const AbilityType abilityType = actoid.getAbilityType();

    if(abilityType == AbilityType::LAY_ON_HANDS)
      {
        combatant->setHasBonusAction(false);
        if(auto resource = actoid.getFactory().getResource())
          {
            if(auto *layOnHands = dynamic_cast<LayOnHands *>(&actoid))
              {
                (*resource)->useResource(layOnHands->removesPoison() ? LayOnHandsFactory::poisonedRemovalCost : layOnHands->getHpAmount());
              }
          }
        return;
      }

    if(abilityType == AbilityType::DIVINE_SMITE)
      {
        combatant->setHasBonusAction(false);
        return;
      }

    // Action category: NOP(0) < type < BONUS_ACTION_DELIMITER
    if(abilityType > AbilityType::NOP && abilityType < AbilityType::BONUS_ACTION_DELIMITER)
      {
        combatant->setHasAction(false);
        switch(abilityType)
          {
          case AbilityType::MELEE_ATTACK:
          case AbilityType::RANGED_ATTACK:
          case AbilityType::RECKLESS_ATTACK:
          case AbilityType::VAMPIRIC_BITE:
          case AbilityType::PARALYZING_MELEE_ATTACK:
          case AbilityType::MENACING_MELEE_ATTACK:
          case AbilityType::MENACING_RANGED_ATTACK:
            if(auto ammo = actoid.getFactory().getResource())
              {
                (*ammo)->useResource();
              }
            combatant->triggerAttackFsm(&actoid.getFactory());
            break;

          case AbilityType::SMITE_MELEE_ATTACK:
            // Divine Smite attack variant: reserves the Bonus Action on top of the Action; the free cast /
            // spell slot is spent by the OnHitDivineSmite rider only when the attack lands. The multiattack FSM
            // is keyed on the original weapon attack, so delegate the transition to the base factory.
            combatant->setHasBonusAction(false);
            if(auto ammo = actoid.getFactory().getResource())
              {
                (*ammo)->useResource();
              }
            if(auto *smite = dynamic_cast<SmiteMeleeAttackFactory *>(&actoid.getFactory()); smite && smite->getBaseFactory())
              {
                combatant->triggerAttackFsm(smite->getBaseFactory());
              }
            else
              {
                combatant->triggerAttackFsm(&actoid.getFactory());
              }
            break;

          case AbilityType::FIREBALL:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(3);
              }
            else
              {
                throw std::runtime_error("Fireball factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::CURE_WOUNDS:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(1);
              }
            else
              {
                throw std::runtime_error("Cure Wounds factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::THUNDERWAVE:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(1);
              }
            else
              {
                throw std::runtime_error("Thunderwave factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::SPIKE_GROWTH:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Spike Growth factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::FAERIE_FIRE:
          case AbilityType::BLESS:
          case AbilityType::GUIDING_BOLT:
          case AbilityType::MAGIC_MISSILE:
          case AbilityType::MAGE_ARMOR:
          case AbilityType::SLEEP:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(1);
              }
            else
              {
                throw std::runtime_error("Level 1 spell factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::FLAMING_SPHERE:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Flaming Sphere factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::MOONBEAM:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Moonbeam factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::SCORCHING_RAY:
          case AbilityType::HOLD_PERSON:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Leveled spell factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;

          case AbilityType::TWINNED_HOLD_PERSON:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Leveled spell factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            combatant->consumeSorceryPoints(1); // Twinned Spell (2024) costs 1 sorcery point.
            break;

          case AbilityType::FIREBOLT:
          case AbilityType::SACRED_FLAME:
          case AbilityType::TOLL_THE_DEAD:
            /*Nothing to do*/
            break;

          default: break;
          }
      }
    // Bonus action category
    else if(abilityType > AbilityType::BONUS_ACTION_DELIMITER && abilityType < AbilityType::REACTION_DELIMITER)
      {
        combatant->setHasBonusAction(false);
        switch(abilityType)
          {
          case AbilityType::BONUS_MELEE_ATTACK:
          case AbilityType::BONUS_RANGED_ATTACK:
          case AbilityType::PAM_BONUS_ATTACK:
            if(auto ammo = actoid.getFactory().getResource())
              {
                (*ammo)->useResource();
              }
            combatant->triggerAttackFsm(&actoid.getFactory());
            break;
          case AbilityType::MOON_WILDSHAPE:
          case AbilityType::WILDSHAPE:
            // Consume one Wild Shape use (per short rest).
            if(auto uses = actoid.getFactory().getResource())
              {
                (*uses)->useResource();
              }
            break;
          case AbilityType::HEALING_WORD:
          case AbilityType::SHIELD_OF_FAITH:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(1);
              }
            else
              {
                throw std::runtime_error("Healing Word factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;
          case AbilityType::RAGE:
            // Consume one Rage use (the animal-aspect variants share a single pool, refreshed on a long rest).
            if(auto uses = actoid.getFactory().getResource())
              {
                (*uses)->useResource();
              }
            break;
          case AbilityType::SECOND_WIND:
            // Consume one Second Wind use (refreshed on a Short or Long Rest). It uses no spell slot.
            if(auto uses = actoid.getFactory().getResource())
              {
                (*uses)->useResource();
              }
            else
              {
                throw std::runtime_error("Second Wind factory must have an associated resource!");
              }
            break;
          case AbilityType::VOW_OF_ENMITY:
            if(auto uses = actoid.getFactory().getResource())
              {
                (*uses)->useResource();
              }
            else
              {
                throw std::runtime_error("Vow of Enmity factory must have an associated Channel Divinity resource!");
              }
            break;
          case AbilityType::MISTY_STEP:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Leveled bonus-action spell factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            break;
          case AbilityType::QUICKENED_SCORCHING_RAY:
          case AbilityType::QUICKENED_HOLD_PERSON:
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(2);
              }
            else
              {
                throw std::runtime_error("Leveled bonus-action spell factory must have an associated resource!");
              }
            combatant->setAlreadyUsedSpellslotThisTurn(true);
            combatant->consumeSorceryPoints(2); // Quickened Spell costs 2 sorcery points.
            break;
          case AbilityType::QUICKENED_FIREBOLT:
          case AbilityType::QUICKENED_RAY_OF_FROST:
            // Quickened cantrips use no spell slot, but still cost 2 sorcery points.
            combatant->consumeSorceryPoints(2);
            break;
          default: break;
          }
      }
    // Reaction category
    else if(abilityType > AbilityType::REACTION_DELIMITER && abilityType < AbilityType::HASTE_ACTION_DELIMITER)
      {
        combatant->setHasReaction(false);
        if(abilityType == AbilityType::RIPOSTE)
          {
            // Riposte (Battle Master maneuver) spends one Superiority Die in addition to the reaction.
            if(auto die = actoid.getFactory().getResource())
              {
                (*die)->useResource();
              }
            combatant->triggerAttackFsm(&actoid.getFactory());
          }
      }
    // Free action category: Action Surge grants an extra Action.
    else if(abilityType == AbilityType::ACTION_SURGE)
      {
        if(auto uses = actoid.getFactory().getResource())
          {
            (*uses)->useResource();
          }
        else
          {
            throw std::runtime_error("Action Surge factory must have an associated resource!");
          }
        combatant->setHasAction(true);
        // The extra Action is a brand-new Action: a combatant with Extra Attack may attack the full number of
        // times again, so restart the multiattack FSM (otherwise it stays at its terminal state and only a single
        // post-surge attack would be feasible).
        combatant->setAttackFsmState(AttackFsm::START);
      }
    // Haste action category
    else if(abilityType > AbilityType::HASTE_ACTION_DELIMITER && abilityType < AbilityType::PASSIVE_DELIMITER)
      {
        combatant->setHasHasteAction(false);
        switch(abilityType)
          {
          case AbilityType::HASTE_MELEE_ATTACK:
          case AbilityType::HASTE_RANGED_ATTACK:
          case AbilityType::HASTE_PARALYZING_MELEE_ATTACK:
            if(auto ammo = actoid.getFactory().getResource())
              {
                (*ammo)->useResource();
              }
            combatant->triggerAttackFsm(&actoid.getFactory());
            break;
          default: break;
          }
      }
    // Movement category
    else if(abilityType == AbilityType::STANDARD_MOVEMENT || abilityType == AbilityType::DISENGAGED_MOVEMENT)
      {
        auto &battleMap = BattleMap::getInstance();
        auto *movement = dynamic_cast<MovementIncrement *>(&actoid);
        int decrement = 1;
        if(combatant->isAffectedByAny({Conditions::PRONE}))
          {
            decrement += 1;
          }
        if(movement)
          {
            Coords targetPosition(battleMap.getCombatantCoordinates(*combatant), movement->getIncrement());
            if(battleMap.isDifficultTerrainAt(targetPosition))
              {
                decrement += 1;
              }
          }
        combatant->setMovement(combatant->getMovement() - decrement);
      }
    else if(abilityType == AbilityType::GET_UP_FROM_PRONE)
      {
        int getUpCost = std::max(1, combatant->getSpeed() / 2);
        combatant->setMovement(combatant->getMovement() - getUpCost);
      }
  }

}
