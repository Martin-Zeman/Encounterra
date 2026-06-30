// darkness.cpp
#include "spells/darkness.hpp"
#include "core/battle_map.hpp"
#include "core/teams.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"
#include "effects/aoe_effect.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include "core/threat_utils.hpp"
#include <algorithm>

namespace enc
{
  namespace
  {
    // Darkness lasts up to 10 minutes; the value of the Blinded condition it imposes is projected over a
    // short planning horizon, mirroring the ROUND_HORIZON multiplier used by other buff/debuff modifiers.
    constexpr int ROUND_HORIZON = 3;

    std::vector<DirectThreatFactory *> getAttackFactories(Combatant *combatant)
    {
      std::vector<DirectThreatFactory *> result;
      auto collect = [&](const std::vector<std::shared_ptr<ActoidFactory>> &factories) {
        for(const auto &factory : factories)
          {
            if(!factory->hasFlag(FactoryFlags::IS_ATTACK_LIKE))
              {
                continue;
              }
            if(auto *threatFactory = dynamic_cast<DirectThreatFactory *>(factory.get()))
              {
                result.push_back(threatFactory);
              }
          }
      };
      collect(combatant->getActionFactoriesConst());
      collect(combatant->getBonusActionFactoriesConst());
      collect(combatant->getHasteActionFactoriesConst());
      return result;
    }

    // The value of Blinding a single enemy with the darkness, as the roll-type changes it produces:
    //  - the Blinded enemy attacks the caster at disadvantage (reduces the damage it deals), and
    //  - a caster with Devil's Sight, who is itself unaffected, attacks the Blinded enemy with advantage.
    double perEnemyThreat(Combatant *caster, Combatant *enemy)
    {
      ThreatModifiers disadvantage;
      disadvantage.set(ThreatModifierType::ROLL_TYPE, RollType::DISADVANTAGE);
      double defensive = 0.0;
      for(auto *attackFactory : getAttackFactories(enemy))
        {
          // Disadvantage yields a negative delta (less expected damage); negate it into a positive benefit.
          defensive = std::max(defensive, -attackFactory->calculateThreatToTargetDelta(caster, disadvantage));
        }

      double offensive = 0.0;
      if(caster->hasPassiveAbility(AbilityType::DEVILS_SIGHT))
        {
          ThreatModifiers advantage;
          advantage.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
          for(auto *attackFactory : getAttackFactories(caster))
            {
              offensive = std::max(offensive, attackFactory->calculateThreatToTargetDelta(enemy, advantage));
            }
        }

      return (defensive + offensive) * ROUND_HORIZON;
    }
  }

  DarknessFactory::DarknessFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : ThreatModifierFactory("DarknessFactory", "Darkness", caster, abilityType), _resource(resource)
  {}

  std::vector<std::shared_ptr<Actoid>> DarknessFactory::createAll(void *previousActionInDag)
  {
    auto &battleMap = BattleMap::getInstance();
    auto [coord, ignoredScore, ignoredValid] = battleMap.findBestPlacementHarmfulCircular(
        _combatant, static_cast<int>(DarknessFactory::range), TRANSLATE_RADIUS.at(DarknessFactory::target));
    return {std::make_shared<Darkness>(coord, *this)};
  }

  std::shared_ptr<Actoid> DarknessFactory::create(void *target) { return std::make_shared<Darkness>(*static_cast<Coord *>(target), *this); }

  double DarknessFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // A creature that can see through magical darkness (Devil's Sight) is never Blinded, so darkness does
    // nothing to it.
    if(target->hasPassiveAbility(AbilityType::DEVILS_SIGHT))
      {
        return 0.0;
      }
    // Disregard allies (and the caster itself): only Blinding enemies has value.
    if(!Teams::getInstance().areEnemies(*_combatant, *target))
      {
        return 0.0;
      }
    return perEnemyThreat(_combatant, target);
  }

  double DarknessFactory::calculateMaxThreat() const
  {
    auto &battleMap = BattleMap::getInstance();
    auto [coord, ignoredScore, ignoredValid] = battleMap.findBestPlacementHarmfulCircular(
        _combatant, static_cast<int>(DarknessFactory::range), TRANSLATE_RADIUS.at(DarknessFactory::target));
    Darkness effect(coord, *this);
    return effect.calculateThreat({});
  }

  Darkness::Darkness(const Coord &coord, const DarknessFactory &factory)
      : Effect(factory._combatant), AoeEffect(factory._combatant),
        Actoid(const_cast<DarknessFactory &>(factory), ActoidFlags::IS_SPELL, factory._abilityType),
        LimitedDurationEffect(factory._combatant, 100), AoeSphericEffect(factory._combatant, coord, TRANSLATE_RADIUS.at(DarknessFactory::target)),
        _coord(coord), _factory(factory)
  {}

  bool Darkness::isBlindedByDarkness(Combatant *combatant) { return !combatant->hasPassiveAbility(AbilityType::DEVILS_SIGHT); }

  void Darkness::onStartOfTurn(Combatant *combatant)
  {
    if(isBlindedByDarkness(combatant))
      {
        combatant->applyCondition(Condition(Conditions::BLINDED, _factory._combatant, this));
      }
  }

  void Darkness::onEndOfTurn(Combatant *combatant) { /* No per-turn effect beyond the persistent Blinded condition. */ }

  void Darkness::onEnter(Combatant *combatant)
  {
    if(isBlindedByDarkness(combatant))
      {
        combatant->applyCondition(Condition(Conditions::BLINDED, _factory._combatant, this));
      }
  }

  void Darkness::onMoveWithin(Combatant *combatant) { /* No effect when moving within the area. */ }

  void Darkness::onExit(Combatant *combatant) { combatant->removeCondition(Conditions::BLINDED, _factory._combatant); }

  void Darkness::activate(const Kwargs &kwargs)
  {
    auto &effectTracker = EffectTracker::getInstance();
    effectTracker.add(Effect::shared_from_this());
    _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
  }

  void Darkness::deactivate() { _factory._combatant->breakConcentration(); }

  bool Darkness::deactivateForCombatant(Combatant *combatant) { throw std::runtime_error("Not implemented"); }

  double Darkness::calculateThreat(const Kwargs &kwargs)
  {
    auto &battleMap = BattleMap::getInstance();
    auto affected = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, DarknessFactory::target, DarknessFactory::type, _coord);

    // The factory's per-target threat already disregards allies and creatures with Devil's Sight, so the
    // area's value is simply the sum over every creature it actually catches.
    double totalThreat = 0.0;
    for(auto *target : affected)
      {
        totalThreat += _factory.calculateThreatToTarget(target, {});
      }
    return totalThreat;
  }

  double Darkness::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::string Darkness::toString() const
  {
    std::stringstream ss;
    ss << _coord;
    return "Darkness at " + ss.str();
  }

  std::string Darkness::shorthandStr() const { return "Darkness"; }

  EffectType Darkness::getEffectType() const { return EffectType::DARKNESS; }

  const CoordVector &Darkness::getAffectedCoords() const { return SphericAoe::getAffectedCoords(); }

  std::optional<CoordVector>
  Darkness::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }

    auto &battleMap = BattleMap::getInstance();

    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_origin), distances, _factory._combatant->getSize(),
                                                       static_cast<int>(DarknessFactory::range), _factory._combatant->_instanceId);
      }

    const Coords &combatantPos = battleMap.getCombatantCoordinates(*_factory._combatant);
    if(getCartesianDistanceCoords(combatantPos, _origin) <= static_cast<double>(DarknessFactory::range))
      {
        return CoordVector{combatantPos.getRoot()};
      }

    return std::nullopt;
  }
}
