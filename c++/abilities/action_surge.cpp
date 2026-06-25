#include "abilities/action_surge.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <algorithm>

namespace enc
{

  ActionSurgeFactory::ActionSurgeFactory(Combatant *combatant, Resource *resource)
      : DirectThreatFactory("ActionSurgeFactory", "Action Surge", combatant, AbilityType::ACTION_SURGE), _resource(resource)
  {
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  int ActionSurgeFactory::getActionSurgeUses(int level) { return level >= 17 ? 2 : 1; }

  std::vector<std::shared_ptr<Actoid>> ActionSurgeFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    result.push_back(std::make_shared<ActionSurge>(*this));
    return result;
  }

  std::shared_ptr<Actoid> ActionSurgeFactory::create(void *target) { return std::make_shared<ActionSurge>(*this); }

  double ActionSurgeFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const { return calculateMaxThreat(); }

  double ActionSurgeFactory::calculateMaxThreat() const
  {
    // Mirrors the Python heuristic: a self-buff worth (at most) one extra action's worth of effort.
    int missingHp = _combatant->getMaxHp() - _combatant->getCurrentHp();
    double healing = percentileRoll(Die{1, 10}, 70) + _combatant->getLevel();
    return std::min({missingHp - healing, static_cast<double>(missingHp), healing});
  }

  std::string ActionSurge::toString() const { return "Action Surge of " + _factory._combatant->_name; }

  std::string ActionSurge::shorthandStr() const { return "Action Surge"; }

  double ActionSurge::calculateThreat(const Kwargs &kwargs) { return _factory.calculateMaxThreat(); }

  std::optional<CoordVector>
  ActionSurge::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    CoordVector coords = {battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
    return coords;
  }
}
