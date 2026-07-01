#include "actions/hide.hpp"
#include "abilities/on_hit_sneak_attack.hpp"
#include "actions/attack.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/threat_modifiers.hpp"
#include "effects/effect_tracker.hpp"
#include <iostream>

namespace enc
{
  std::vector<std::shared_ptr<Actoid>> HideFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    if(_combatant->getSwallower() != nullptr)
      {
        return result;
      }
    EffectTracker &effectTracker = EffectTracker::getInstance();
    for(Combatant *enemy : Teams::getInstance().getAliveNonSwallowedEnemies(*_combatant))
      {
        if(!effectTracker.isCombatantHiddenFrom(_combatant, enemy))
          {
            result.push_back(std::make_shared<Hide>(*this, enemy));
          }
      }
    return result;
  }

  std::shared_ptr<Actoid> HideFactory::create(void *target)
  {
    return std::make_shared<Hide>(*this, static_cast<Combatant *>(target));
  }

  Hide::Hide(HideFactory &factory, Combatant *target)
      : Effect(factory.getCombatant(), target), AttackThreatModifier(factory, ActoidFlags::IS_HIDE, factory.getAbilityType()),
        CombatantEffect(factory.getCombatant(), {factory.getCombatant()}), _factory(factory)
  {}

  EffectType Hide::getEffectType() const { return EffectType::HIDE; }

  void Hide::activate(const Kwargs &kwargs)
  {
    Combatant *rogue = _factory.getCombatant();
    // 2024: the Hide action requires a successful Dexterity (Stealth) check against the Passive Perception of
    // the creature the rogue is trying to hide from. On a success the rogue has the Invisible-granting Hidden
    // condition with respect to that creature until it is next seen.
    if(rollAbilityCheck(rogue->getStealth(), _target->getPassivePerception() + 1, RollType::STRAIGHT))
      {
        std::cout << rogue->_name << " hides from " << _target->_name << std::endl;
        EffectTracker::getInstance().add(shared_from_this());
      }
    else
      {
        std::cout << rogue->_name << " fails to hide from " << _target->_name << std::endl;
      }
  }

  void Hide::deactivate()
  {
    std::cout << _factory.getCombatant()->_name << " is no longer hidden from " << _target->_name << std::endl;
  }

  bool Hide::deactivateForCombatant(Combatant *combatant)
  {
    deactivate();
    return false;
  }

  std::string Hide::prefix() const
  {
    switch(_factory.getAbilityType())
      {
      case AbilityType::CUNNING_HIDE:
        return "Cunning ";
      case AbilityType::HASTE_HIDE:
        return "Hasted ";
      default:
        return "";
      }
  }

  std::string Hide::toString() const
  {
    return prefix() + "Hide of " + _factory.getCombatant()->_name + " from " + _target->_name;
  }

  std::string Hide::shorthandStr() const { return prefix() + "Hide"; }

  std::optional<CoordVector>
  Hide::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    Combatant *rogue = _factory.getCombatant();
    if(rogue->getSwallower() != nullptr)
      {
        return std::nullopt;
      }
    BattleMap &battleMap = BattleMap::getInstance();

    // Unchanged geometry: a rogue that is free to move may hide from any square out of the target's line of
    // sight (Visibility::NONE). This reuses the existing visibility dictionary.
    if(!rogue->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        CoordVector eligible;
        for(const auto &[coord, visDict] : battleMap.getVisibilityDictForAllCoords())
          {
            auto it = visDict.find(_target);
            if(it != visDict.end() && it->second == Visibility::NONE)
              {
                eligible.push_back(coord);
              }
          }
        return eligible;
      }

    // While Grappled/Grappling/Restrained the rogue cannot move; it may only hide if its current square is
    // already out of the target's line of sight.
    const Coord currCoord = battleMap.getCombatantCoordinates(*rogue).getRoot();
    if(battleMap.getVisibilityFromCoord(currCoord, _target) == Visibility::NONE)
      {
        return CoordVector{currCoord};
      }
    return std::nullopt;
  }

  double Hide::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs)
  {
    auto *concreteAttack = dynamic_cast<Attack *>(attack);
    if(concreteAttack == nullptr || &concreteAttack->getTarget() != _target)
      {
        return 0.0;
      }
    AttackFactory &factory = concreteAttack->getAttackFactory();
    const bool attackLike = factory.hasFlag(FactoryFlags::IS_ATTACK_LIKE) || factory.hasFlag(FactoryFlags::USES_DEX)
                            || factory.hasFlag(FactoryFlags::IS_RANGED);
    if(!attackLike || attacker->getMovement() <= 0)
      {
        return 0.0;
      }

    // Hiding grants Advantage on the rogue's next attack against the target.
    ThreatModifiers mods;
    mods.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    double threatAcc = 0.0;
    if(auto *directThreat = dynamic_cast<DirectThreat *>(attack))
      {
        threatAcc = directThreat->calculateThreatDelta(mods);
      }

    // If an ally is already adjacent to the target, Sneak Attack would apply anyway, so the Advantage's only
    // value is the improved hit chance already counted above.
    if(BattleMap::getInstance().isAllyAdjacentToTarget(*attacker, *_target))
      {
        return threatAcc;
      }

    // Otherwise the Advantage is what unlocks Sneak Attack: add the expected extra Sneak Attack damage. Mirrors
    // Python Hide.calculate_threat_for_attack, which credits the sneak on-hit with roll_type=ADVANTAGE.
    for(const auto &onHit : factory.getOnHits())
      {
        if(auto *sneak = dynamic_cast<OnHitSneakAttack *>(onHit.get()))
          {
            int rollNeeded = _target->getAC() - factory.getToHit();
            int advDelta = getRollTypeDelta(RollType::ADVANTAGE, rollNeeded);
            threatAcc += calcPHit(factory.getToHit() + advDelta, _target->getAC())
                         * sneak->calculateThreat(attacker, _target, RollType::ADVANTAGE);
        }
      }
    return threatAcc;
  }
}
