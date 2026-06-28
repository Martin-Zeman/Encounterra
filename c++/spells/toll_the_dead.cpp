#include "spells/toll_the_dead.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>

namespace enc
{
  Die TollTheDeadFactory::getDmgDice(int level, bool wounded)
  {
    uint8_t sides = wounded ? 12 : 8;
    if(level >= 1 && level <= 4) return {1, sides};
    if(level >= 5 && level <= 10) return {2, sides};
    if(level >= 11 && level <= 16) return {3, sides};
    if(level >= 17) return {4, sides};
    throw std::runtime_error("Incorrect caster level of Toll the Dead");
  }

  TollTheDeadFactory::TollTheDeadFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("TollTheDeadFactory", "Toll the Dead", caster, abilityType), _dc(dc), _resource(resource)
  {}

  std::vector<Combatant *> TollTheDeadFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(TollTheDeadFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> TollTheDeadFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<TollTheDead>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> TollTheDeadFactory::create(void *target)
  {
    return std::make_shared<TollTheDead>(*static_cast<Combatant *>(target), *this);
  }

  double TollTheDeadFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(TollTheDeadFactory::range))
      {
        return 0.0;
      }
    Die dmgDice = getDmgDice(_combatant->getLevel(), target->getCurrentHp() < target->getMaxHp());
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, {dmgDice}, false, target->getSavingThrow(TollTheDeadFactory::savingThrow),
                                    target->isImmuneTo(TollTheDeadFactory::dmgType), target->isResistantTo(TollTheDeadFactory::dmgType)));
  }

  double TollTheDeadFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    int dcBonus = modifiers.getOrDefault(ThreatModifierType::SAVE_DC, 0);
    Die dmgDice = getDmgDice(_combatant->getLevel(), target->getCurrentHp() < target->getMaxHp());
    double modified = meanDmgDcAttack(_dc + dcBonus, {dmgDice}, false, target->getSavingThrow(TollTheDeadFactory::savingThrow),
                                      target->isImmuneTo(TollTheDeadFactory::dmgType), target->isResistantTo(TollTheDeadFactory::dmgType));
    double baseline = meanDmgDcAttack(_dc, {dmgDice}, false, target->getSavingThrow(TollTheDeadFactory::savingThrow),
                                      target->isImmuneTo(TollTheDeadFactory::dmgType), target->isResistantTo(TollTheDeadFactory::dmgType));
    return modified - baseline;
  }

  double TollTheDeadFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string TollTheDead::toString() const { return "Toll the Dead at " + _target._name; }

  std::string TollTheDead::shorthandStr() const { return "Toll the Dead"; }

  Die TollTheDead::getDmgDice() const
  {
    return TollTheDeadFactory::getDmgDice(_factory._combatant->getLevel(), _target.getCurrentHp() < _target.getMaxHp());
  }

  double TollTheDead::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double TollTheDead::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector> TollTheDead::getEligibleCoords(const blaze::DynamicVector<int> &distances,
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
                                                       static_cast<int>(TollTheDeadFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(TollTheDeadFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }
}
