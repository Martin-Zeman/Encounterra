#include "abilities/roar.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/threat_utils.hpp"
#include <algorithm>

namespace enc
{
  RoarFactory::RoarFactory(Combatant *combatant, int dc, int range)
      : DirectThreatFactory("RoarFactory", "Roar", combatant, AbilityType::ROAR), _dc(dc), _range(range)
  {
    setFlag(FactoryFlags::TARGETS_SELF);
  }

  std::vector<Combatant *> RoarFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> result;
    for(auto *enemy : teams.getAliveNonSwallowedEnemies(*_combatant))
      {
        if(battleMap.getCartesianDistanceCombatants(*_combatant, *enemy) <= static_cast<double>(_range))
          {
            result.push_back(enemy);
          }
      }
    return result;
  }

  std::vector<std::shared_ptr<Actoid>> RoarFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<Roar>(*this)};
  }

  std::shared_ptr<Actoid> RoarFactory::create(void *target) { return std::make_shared<Roar>(*this); }

  double RoarFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) > static_cast<double>(_range))
      {
        return 0.0;
      }
    return getSavingThrowFailProb(_dc, target->getSavingThrow(savingThrow)) * RoarFactory::THREAT_PER_TARGET;
  }

  double RoarFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double RoarFactory::calculateMaxThreat() const
  {
    double acc = 0.0;
    for(auto *target : getEligibleTargets())
      {
        acc += calculateThreatToTarget(target, Kwargs());
      }
    return acc;
  }

  std::string Roar::toString() const { return "Roar by " + _factory._combatant->_name; }

  std::string Roar::shorthandStr() const { return "Roar"; }

  std::optional<CoordVector>
  Roar::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // Roar is performed in place; it is always available from the roarer's current position.
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*_factory._combatant).getRoot()};
  }

  double Roar::calculateThreat(const Kwargs &kwargs)
  {
    double acc = 0.0;
    for(auto *target : _factory.getEligibleTargets())
      {
        acc += _factory.calculateThreatToTarget(target, kwargs);
      }
    return acc;
  }

  double Roar::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  void RoarFrightenedEffect::activate(const Kwargs &kwargs)
  {
    for(auto *combatant : _combatants)
      {
        if(!combatant->isAffectedBy(Conditions::FRIGHTENED))
          {
            combatant->applyCondition(Condition(Conditions::FRIGHTENED, _initiator, this));
          }
      }
  }

  void RoarFrightenedEffect::deactivate()
  {
    for(auto *combatant : _combatants)
      {
        combatant->removeCondition(Conditions::FRIGHTENED, _initiator);
      }
    _combatants.clear();
  }

  bool RoarFrightenedEffect::deactivateForCombatant(Combatant *combatant)
  {
    auto it = std::find(_combatants.begin(), _combatants.end(), combatant);
    if(it != _combatants.end())
      {
        combatant->removeCondition(Conditions::FRIGHTENED, _initiator);
        _combatants.erase(it);
      }
    return _combatants.empty();
  }
}
