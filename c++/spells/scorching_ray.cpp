#include "spells/scorching_ray.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>

namespace enc
{

  ScorchingRayFactory::ScorchingRayFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("ScorchingRayFactory", "Scorching Ray", caster, abilityType), _toHit(toHit), _resource(resource),
        _dmgDice(ScorchingRayFactory::rayDmgDice)
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant *> ScorchingRayFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(ScorchingRayFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> ScorchingRayFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<ScorchingRay>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> ScorchingRayFactory::create(void *target)
  {
    return std::make_shared<ScorchingRay>(*static_cast<Combatant *>(target), *this);
  }

  double ScorchingRayFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower())
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(ScorchingRayFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        double singleRay = meanDmg(toHitTotal, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(ScorchingRayFactory::dmgType),
                                   target->isResistantTo(ScorchingRayFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
        return ScorchingRayFactory::numRays * singleRay;
      }

    return 0;
  }

  double ScorchingRayFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    if(target->isImmuneTo(ScorchingRayFactory::dmgType))
      {
        return 0;
      }

    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = targetAC + target->getAC();
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    int needToRollAtLeast = std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20));
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(needToRollAtLeast);
    double totalCrit = ROLL_TYPE_CRIT_DELTA.at(rollType);

    double modifiedThreat = ScorchingRayFactory::numRays
                            * meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC, target->isImmuneTo(ScorchingRayFactory::dmgType),
                                      target->isResistantTo(ScorchingRayFactory::dmgType), totalCrit);

    double originalThreat = ScorchingRayFactory::numRays
                            * meanDmg(_toHit, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(ScorchingRayFactory::dmgType),
                                      target->isResistantTo(ScorchingRayFactory::dmgType), 1);

    return modifiedThreat - originalThreat;
  }

  double ScorchingRayFactory::calculateMaxThreat() const
  {
    auto eligibleTargets = getEligibleTargets();
    double maxThreat = std::numeric_limits<double>::lowest();
    for(const auto &target : eligibleTargets)
      {
        double threat = ScorchingRay(*target, *this).calculateThreat(Kwargs());
        maxThreat = std::max(maxThreat, threat);
      }
    return eligibleTargets.empty() ? 0 : maxThreat;
  }

  std::string ScorchingRay::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_SCORCHING_RAY) ? "Quickened " : "";
    return prefix + "Scorching Ray at " + _target._name;
  }

  std::string ScorchingRay::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_SCORCHING_RAY) ? "Quickened " : "";
    return prefix + "Scorching Ray";
  }

  double ScorchingRay::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto rollType = battleMap.isEnemyAdjacent(*_factory._combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    int acDifference = std::max(0, std::min(20, _target.getAC() - _factory._toHit));
    int toHitTotal = _factory._toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
    double singleRay = meanDmg(toHitTotal, {_factory._dmgDice}, 0, _target.getAC(), _target.isImmuneTo(ScorchingRayFactory::dmgType),
                               _target.isResistantTo(ScorchingRayFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
    return ScorchingRayFactory::numRays * singleRay;
  }

  double ScorchingRay::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector>
  ScorchingRay::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    ScorchingRayFactory &factory = dynamic_cast<ScorchingRayFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).getRoot();
    if(swallower)
      {
        if(swallower == &_target)
          {
            CoordVector coords = {currCoord};
            return coords;
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                       static_cast<int>(ScorchingRayFactory::range), factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= static_cast<int>(ScorchingRayFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return {};
  }
}
