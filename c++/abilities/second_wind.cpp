#include "abilities/second_wind.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <algorithm>

namespace enc
{

  SecondWindFactory::SecondWindFactory(Combatant *combatant, Resource *resource, int level, Die healDice)
      : DirectThreatFactory("SecondWindFactory", "Second Wind", combatant, AbilityType::SECOND_WIND), _resource(resource), _level(level),
        _healDice(healDice)
  {
    // Second Wind only ever targets the fighter itself, so it does not depend on a chosen target cell.
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  std::vector<Combatant *> SecondWindFactory::getEligibleTargets() const { return {_combatant}; }

  std::vector<std::shared_ptr<Actoid>> SecondWindFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    result.push_back(std::make_shared<SecondWind>(*_combatant, *this));
    return result;
  }

  std::shared_ptr<Actoid> SecondWindFactory::create(void *target)
  {
    // Second Wind always heals the fighter itself regardless of the passed target.
    return std::make_shared<SecondWind>(*_combatant, *this);
  }

  double SecondWindFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    int missingHp = _combatant->getMaxHp() - _combatant->getCurrentHp();
    return std::min(static_cast<double>(missingHp), avgRoll(_healDice) + _level);
  }

  double SecondWindFactory::calculateMaxThreat() const { return avgRoll(_healDice) + _level; }

  std::string SecondWind::toString() const { return shorthandStr() + " on " + _target._name; }

  std::string SecondWind::shorthandStr() const { return "Second Wind"; }

  double SecondWind::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  std::optional<CoordVector>
  SecondWind::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    CoordVector coords = {battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
    return coords;
  }
}
