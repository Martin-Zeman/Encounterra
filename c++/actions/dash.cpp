#include "actions/dash.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include <algorithm>
#include <vector>

namespace enc
{
  std::vector<std::shared_ptr<Actoid>> DashFactory::createAll(void *previousActionInDag)
  {
    return {std::make_shared<Dash>(static_cast<ActoidFactory &>(*this))};
  }

  std::shared_ptr<Actoid> DashFactory::create(void *target) { return std::make_shared<Dash>(static_cast<ActoidFactory &>(*this)); }

  std::optional<CoordVector>
  Dash::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    // Mirrors Python actions.dash.Dash.get_eligible_coords. Dashing is location independent, so it can be taken
    // from ANY square the combatant can reach this turn (this is what lets a fleeing combatant Disengage, move
    // far, then Dash). It is unavailable while Grappled/Grappling/Restrained/Swallowed.
    Combatant *combatant = _factory.getCombatant();
    if(combatant->getSwallower() != nullptr
       || combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return std::nullopt;
      }
    return BattleMap::getInstance().getAllAccessibleCoords(shortestPaths, *combatant);
  }

  std::string Dash::toString() const
  {
    return _abilityType == AbilityType::CUNNING_DASH ? "Cunning Dash" : "Dash";
  }

  double Dash::calculateThreat(const Kwargs &kwargs)
  {
    // Mirrors Python actions.dash.Dash.calculate_threat. The planner threads the cumulative-threat-along-path
    // array it computed for this sequence's destination in via the "movementThreat" kwarg (only dash actoids
    // ask for it, so the common threat path never pays for building it). movementThreat[i] is the projected
    // threat (negative) of standing i cells along the path; index 0 is the current square.
    auto it = kwargs.find("movementThreat");
    if(it == kwargs.end())
      {
        return 0.0;
      }
    const auto *movementThreat = std::any_cast<const std::vector<double> *>(it->second);
    if(movementThreat == nullptr || movementThreat->empty())
      {
        return 0.0;
      }

    Combatant *combatant = _factory.getCombatant();
    const int lastIdx = static_cast<int>(movementThreat->size()) - 1;
    const int movement = combatant->getMovement();
    const int speed = combatant->getSpeed();

    if(_abilityType == AbilityType::AGGRESSIVE)
      {
        // Aggressive movement (Barbarian): we always want it when the destination can't be reached with the
        // current movement budget (the "move towards an enemy" intent is assumed), otherwise it is discouraged.
        return lastIdx > movement ? 1.0 : -1.0;
      }

    // Defensive dash: compare the threat we'd be exposed to stopping at our normal movement limit against the
    // threat at movement + speed (one extra Dash of distance) further along the same path. Only credit the
    // reduction (max(0, ...)); we don't want Dash to weigh in when it would merely carry us deeper into danger.
    const double baseline = -1.0 * (*movementThreat)[std::min(movement, lastIdx)];
    const double modified = -1.0 * (*movementThreat)[std::min(movement + speed, lastIdx)];
    return std::max(0.0, baseline - modified);
  }
}
