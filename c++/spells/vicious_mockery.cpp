#include "spells/vicious_mockery.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>
#include <limits>

namespace enc
{
  Die ViciousMockeryFactory::getDmgDice(int level)
  {
    if(level >= 1 && level <= 4) return {1, 6};
    if(level >= 5 && level <= 10) return {2, 6};
    if(level >= 11 && level <= 16) return {3, 6};
    if(level >= 17) return {4, 6};
    throw std::runtime_error("Incorrect caster level of Vicious Mockery");
  }

  ViciousMockeryFactory::ViciousMockeryFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("ViciousMockeryFactory", "Vicious Mockery", caster, abilityType), _dc(dc), _resource(resource),
        _dmgDice(ViciousMockeryFactory::getDmgDice(caster->getLevel()))
  {}

  std::vector<Combatant *> ViciousMockeryFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(ViciousMockeryFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> ViciousMockeryFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<ViciousMockery>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> ViciousMockeryFactory::create(void *target)
  {
    return std::make_shared<ViciousMockery>(*static_cast<Combatant *>(target), *this);
  }

  double ViciousMockeryFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(ViciousMockeryFactory::range))
      {
        return 0.0;
      }
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(ViciousMockeryFactory::savingThrow),
                                    target->isImmuneTo(ViciousMockeryFactory::dmgType), target->isResistantTo(ViciousMockeryFactory::dmgType)));
  }

  double ViciousMockeryFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    int dcBonus = modifiers.getOrDefault(ThreatModifierType::SAVE_DC, 0);
    double modified = meanDmgDcAttack(_dc + dcBonus, {_dmgDice}, false, target->getSavingThrow(ViciousMockeryFactory::savingThrow),
                                      target->isImmuneTo(ViciousMockeryFactory::dmgType), target->isResistantTo(ViciousMockeryFactory::dmgType));
    double baseline = meanDmgDcAttack(_dc, {_dmgDice}, false, target->getSavingThrow(ViciousMockeryFactory::savingThrow),
                                      target->isImmuneTo(ViciousMockeryFactory::dmgType), target->isResistantTo(ViciousMockeryFactory::dmgType));
    return modified - baseline;
  }

  double ViciousMockeryFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string ViciousMockery::toString() const { return "Vicious Mockery at " + _target._name; }

  std::string ViciousMockery::shorthandStr() const { return "Vicious Mockery"; }

  double ViciousMockery::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double ViciousMockery::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector> ViciousMockery::getEligibleCoords(const blaze::DynamicVector<int> &distances,
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
                                                       static_cast<int>(ViciousMockeryFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(ViciousMockeryFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
