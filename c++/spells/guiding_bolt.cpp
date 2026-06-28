#include "spells/guiding_bolt.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>

namespace enc
{
  GuidingBoltFactory::GuidingBoltFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("GuidingBoltFactory", "Guiding Bolt", caster, abilityType), _toHit(toHit), _resource(resource)
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant *> GuidingBoltFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(GuidingBoltFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> GuidingBoltFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<GuidingBolt>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> GuidingBoltFactory::create(void *target)
  {
    return std::make_shared<GuidingBolt>(*static_cast<Combatant *>(target), *this);
  }

  double GuidingBoltFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(GuidingBoltFactory::range))
      {
        return 0.0;
      }
    auto rollType = BattleMap::getInstance().isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
    int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmg(toHitTotal, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(GuidingBoltFactory::dmgType),
                            target->isResistantTo(GuidingBoltFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType)))
           + GuidingBoltFactory::ADVANTAGE_THREAT;
  }

  double GuidingBoltFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = target->getAC() + targetAC;
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    int needToRollAtLeast = std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20));
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(needToRollAtLeast);

    double modified = meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC, target->isImmuneTo(GuidingBoltFactory::dmgType),
                              target->isResistantTo(GuidingBoltFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
    double baseline = meanDmg(_toHit, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(GuidingBoltFactory::dmgType),
                              target->isResistantTo(GuidingBoltFactory::dmgType), 1);
    return modified - baseline;
  }

  double GuidingBoltFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string GuidingBolt::toString() const { return "Guiding Bolt at " + _target._name; }

  std::string GuidingBolt::shorthandStr() const { return "Guiding Bolt"; }

  double GuidingBolt::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double GuidingBolt::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector> GuidingBolt::getEligibleCoords(const blaze::DynamicVector<int> &distances,
                                                            const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory._combatant;
    Combatant *swallower = caster->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(swallower)
      {
        return swallower == &_target ? CoordVector{currCoord} : CoordVector{};
      }
    if(!caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, caster->getSize(),
                                                       static_cast<int>(GuidingBoltFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(GuidingBoltFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
