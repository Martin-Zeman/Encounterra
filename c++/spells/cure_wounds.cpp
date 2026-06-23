#include "spells/cure_wounds.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <algorithm>
#include <limits>

namespace enc
{

  CureWoundsFactory::CureWoundsFactory(Combatant *caster, Resource *resource, int mod, AbilityType abilityType, Die healDice)
      : DirectThreatFactory("CureWoundsFactory", "Cure Wounds", caster, abilityType), _resource(resource), _mod(mod), _healDice(healDice)
  {}

  std::vector<Combatant *> CureWoundsFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(_combatant->getSwallower())
      {
        return {};
      }
    std::vector<Combatant *> targets = battleMap.getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(CureWoundsFactory::range));
    targets.push_back(_combatant);
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> CureWoundsFactory::createAll(void *previousActionInDag)
  {
    auto targets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targets.size());
    for(const auto &t : targets)
      {
        result.push_back(std::make_shared<CureWounds>(*t, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> CureWoundsFactory::create(void *target)
  {
    return std::make_shared<CureWounds>(*static_cast<Combatant *>(target), *this);
  }

  double CureWoundsFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower())
      {
        return 0.0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(CureWoundsFactory::range))
      {
        int missingHp = target->getMaxHp() - target->getCurrentHp();
        return std::min(static_cast<double>(missingHp), avgRoll(_healDice) + _mod);
      }
    return 0.0;
  }

  double CureWoundsFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double CureWoundsFactory::calculateMaxThreat() const { return avgRoll(_healDice) + _mod; }

  std::string CureWounds::toString() const { return shorthandStr() + " on " + _target._name; }

  std::string CureWounds::shorthandStr() const { return "Cure Wounds"; }

  double CureWounds::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double CureWounds::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector>
  CureWounds::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }
    Coord currCoord = battleMap.getCombatantCoordinates(*_factory._combatant).getRoot();
    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, _factory._combatant->getSize(),
                                                       static_cast<int>(CureWoundsFactory::range), _factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*_factory._combatant, _target) <= static_cast<int>(CureWoundsFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return std::nullopt;
  }
}
