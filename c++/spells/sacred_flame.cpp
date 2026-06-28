#include "spells/sacred_flame.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>
#include <limits>

namespace enc
{
  Die SacredFlameFactory::getDmgDice(int level)
  {
    if(level >= 1 && level <= 4) return {1, 8};
    if(level >= 5 && level <= 10) return {2, 8};
    if(level >= 11 && level <= 16) return {3, 8};
    if(level >= 17) return {4, 8};
    throw std::runtime_error("Incorrect caster level of Sacred Flame");
  }

  SacredFlameFactory::SacredFlameFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("SacredFlameFactory", "Sacred Flame", caster, abilityType), _dc(dc), _resource(resource),
        _dmgDice(SacredFlameFactory::getDmgDice(caster->getLevel()))
  {}

  std::vector<Combatant *> SacredFlameFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(SacredFlameFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> SacredFlameFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<SacredFlame>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> SacredFlameFactory::create(void *target)
  {
    return std::make_shared<SacredFlame>(*static_cast<Combatant *>(target), *this);
  }

  double SacredFlameFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(SacredFlameFactory::range))
      {
        return 0.0;
      }
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(SacredFlameFactory::savingThrow),
                                    target->isImmuneTo(SacredFlameFactory::dmgType), target->isResistantTo(SacredFlameFactory::dmgType)));
  }

  double SacredFlameFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    int dcBonus = modifiers.getOrDefault(ThreatModifierType::SAVE_DC, 0);
    double modified = meanDmgDcAttack(_dc + dcBonus, {_dmgDice}, false, target->getSavingThrow(SacredFlameFactory::savingThrow),
                                      target->isImmuneTo(SacredFlameFactory::dmgType), target->isResistantTo(SacredFlameFactory::dmgType));
    double baseline = meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(SacredFlameFactory::savingThrow),
                                      target->isImmuneTo(SacredFlameFactory::dmgType), target->isResistantTo(SacredFlameFactory::dmgType));
    return modified - baseline;
  }

  double SacredFlameFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string SacredFlame::toString() const { return "Sacred Flame at " + _target._name; }

  std::string SacredFlame::shorthandStr() const { return "Sacred Flame"; }

  double SacredFlame::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double SacredFlame::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector> SacredFlame::getEligibleCoords(const blaze::DynamicVector<int> &distances,
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
                                                       static_cast<int>(SacredFlameFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(SacredFlameFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
