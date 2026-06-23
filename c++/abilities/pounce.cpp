#include "abilities/pounce.hpp"
#include "abilities/on_hit_prone.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "core/threat_utils.hpp"
#include <algorithm>

namespace enc
{
  PounceFactory::PounceFactory(Combatant *combatant, std::shared_ptr<MeleeAttackFactory> primary,
                               std::shared_ptr<MeleeAttackFactory> secondary, int distance)
      : DirectThreatFactory("PounceFactory", "Pounce", combatant, AbilityType::POUNCE), _primary(std::move(primary)),
        _secondary(std::move(secondary)), _distance(distance)
  {
    setFlag(FactoryFlags::IS_MELEE);
  }

  void PounceFactory::setCombatant(Combatant *combatant)
  {
    ActoidFactory::setCombatant(combatant);
    if(_primary)
      _primary->setCombatant(combatant);
    if(_secondary)
      _secondary->setCombatant(combatant);
  }

  std::vector<Combatant *> PounceFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {};
      }
    // Targets that the beast is not already adjacent to (it needs room to charge `distance` cells).
    return BattleMap::getInstance().getNonSwallowedEnemiesWithoutHopDistance(_combatant, _distance - 1);
  }

  std::vector<std::shared_ptr<Actoid>> PounceFactory::createAll(void *previousActionInDag)
  {
    auto targets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targets.size());
    for(auto *t : targets)
      {
        result.push_back(std::make_shared<Pounce>(t, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> PounceFactory::create(void *target)
  {
    return std::make_shared<Pounce>(static_cast<Combatant *>(target), *this);
  }

  double PounceFactory::proneFailProb(Combatant *target) const
  {
    if(!_primary)
      return 0.0;
    for(const auto &onHit : _primary->getOnHits())
      {
        if(auto *prone = dynamic_cast<OnHitProne *>(onHit.get()))
          {
            if(!prone->requiresSave())
              {
                // Automatic prone: certain unless the target is too large to be knocked Prone.
                return target->getSize() > prone->getMaxSize() ? 0.0 : 1.0;
              }
            return 1.0 - getSavingThrowSuccessProb(prone->getDc(), target->getSavingThrow(prone->getSaveType()));
          }
      }
    return 0.0;
  }

  double PounceFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    double threat = _primary ? _primary->calculateThreatToTarget(target, kwargs) : 0.0;
    if(_secondary)
      {
        threat += proneFailProb(target) * _secondary->calculateThreatToTarget(target, kwargs);
      }
    return threat;
  }

  double PounceFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    double delta = _primary ? _primary->calculateThreatToTargetDelta(target, modifiers) : 0.0;
    if(_secondary)
      {
        delta += proneFailProb(target) * _secondary->calculateThreatToTargetDelta(target, modifiers);
      }
    return delta;
  }

  double PounceFactory::calculateMaxThreat() const
  {
    auto targets = getEligibleTargets();
    double best = 0.0;
    for(auto *t : targets)
      {
        best = std::max(best, calculateThreatToTarget(t, Kwargs()));
      }
    return best;
  }

  std::string Pounce::toString() const { return "Pounce on " + (_target ? _target->_name : std::string("?")); }

  std::string Pounce::shorthandStr() const { return "Pounce"; }

  bool Pounce::isStraightLinePath(const Coord &endCoord, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    const Coord &source = battleMap.getCombatantCoordinates(*_factory._combatant).getRoot();
    CoordVector path = battleMap.reconstructFromShortestPath(shortestPaths, source, endCoord);
    if(path.empty())
      {
        return false;
      }
    return BattleMap::isPathStraight(path, _factory._distance);
  }

  std::optional<CoordVector>
  Pounce::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        // Free landing cells adjacent (hop range 1) to the target, restricted to those reachable by a straight charge.
        CoordVector all = battleMap.getFreeCoordsInHopRange(battleMap.getCombatantCoordinates(*_target).get(), distances,
                                                            _factory._combatant->getSize(), 1, _factory._combatant->_instanceId);
        CoordVector eligible;
        for(const auto &coord : all)
          {
            if(isStraightLinePath(coord, shortestPaths))
              {
                eligible.push_back(coord);
              }
          }
        return eligible;
      }
    else if(battleMap.getHopDistanceCombatants(*_factory._combatant, *_target) >= _factory._distance)
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }
    return std::nullopt;
  }

  double Pounce::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(_target, kwargs); }

  double Pounce::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(_target, modifiers);
  }
}
