#include "core/resources.hpp"
#include "core/interfaces.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include "actions/action_types.hpp"
#include "actions/movement.hpp"

namespace enc
{

  void useResources(Combatant *combatant, Actoid &actoid)
  {
    const AbilityType abilityType = actoid.getAbilityType();

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
            if(auto resource = actoid.getFactory().getResource())
              {
                (*resource)->useResource(1);
              }
            else
              {
                throw std::runtime_error("Faerie Fire factory must have an associated resource!");
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

          case AbilityType::FIREBOLT: /*Nothing to do*/ break;

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
          default: break;
          }
      }
    // Reaction category
    else if(abilityType > AbilityType::REACTION_DELIMITER && abilityType < AbilityType::HASTE_ACTION_DELIMITER)
      {
        combatant->setHasReaction(false);
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
        combatant->setMovement(combatant->getMovement() - combatant->getSpeed() / 2);
      }
  }

}
