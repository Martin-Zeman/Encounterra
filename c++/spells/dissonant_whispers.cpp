#include "spells/dissonant_whispers.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/threat_utils.hpp"
#include "core/geometry.hpp"
#include <algorithm>
#include <limits>

namespace enc
{
  DissonantWhispersFactory::DissonantWhispersFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("DissonantWhispersFactory", "Dissonant Whispers", caster, abilityType), _dc(dc), _resource(resource)
  {}

  std::vector<Combatant *> DissonantWhispersFactory::getEligibleTargets() const
  {
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return BattleMap::getInstance().getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(DissonantWhispersFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> DissonantWhispersFactory::createAll(void *previousActionInDag)
  {
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *target : getEligibleTargets())
      {
        result.push_back(std::make_shared<DissonantWhispers>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> DissonantWhispersFactory::create(void *target)
  {
    return std::make_shared<DissonantWhispers>(*static_cast<Combatant *>(target), *this);
  }

  double DissonantWhispersFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    if(BattleMap::getInstance().getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(DissonantWhispersFactory::range))
      {
        return 0.0;
      }
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, {dmgDice}, true, target->getSavingThrow(DissonantWhispersFactory::savingThrow),
                                    target->isImmuneTo(DissonantWhispersFactory::dmgType), target->isResistantTo(DissonantWhispersFactory::dmgType)));
  }

  double DissonantWhispersFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    int dcBonus = modifiers.getOrDefault(ThreatModifierType::SAVE_DC, 0);
    double modified = meanDmgDcAttack(_dc + dcBonus, {dmgDice}, true, target->getSavingThrow(DissonantWhispersFactory::savingThrow),
                                      target->isImmuneTo(DissonantWhispersFactory::dmgType), target->isResistantTo(DissonantWhispersFactory::dmgType));
    double baseline = meanDmgDcAttack(_dc, {dmgDice}, true, target->getSavingThrow(DissonantWhispersFactory::savingThrow),
                                      target->isImmuneTo(DissonantWhispersFactory::dmgType), target->isResistantTo(DissonantWhispersFactory::dmgType));
    return modified - baseline;
  }

  double DissonantWhispersFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(auto *target : getEligibleTargets())
      {
        maxThreat = std::max(maxThreat, calculateThreatToTarget(target, {}));
      }
    return maxThreat;
  }

  std::string DissonantWhispers::toString() const { return "Dissonant Whispers at " + _target._name; }

  std::string DissonantWhispers::shorthandStr() const { return "Dissonant Whispers"; }

  double DissonantWhispers::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double DissonantWhispers::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector> DissonantWhispers::getEligibleCoords(const blaze::DynamicVector<int> &distances,
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
                                                       static_cast<int>(DissonantWhispersFactory::range), caster->_instanceId);
      }
    if(battleMap.getCartesianDistanceCombatants(*caster, _target) <= static_cast<int>(DissonantWhispersFactory::range))
      {
        return CoordVector{currCoord};
      }
    return CoordVector{};
  }

  void DissonantWhispers::forceFlee(Combatant *caster)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    // A grappled or restrained target cannot move even when compelled to flee.
    if(_target.isAffectedByAny({Conditions::GRAPPLED, Conditions::RESTRAINED, Conditions::PARALYZED, Conditions::STUNNED, Conditions::PETRIFIED}))
      {
        return;
      }
    const int speed = _target.getSpeed();
    if(speed <= 0)
      {
        return;
      }

    const Coords casterCoords = battleMap.getCombatantCoordinates(*caster);
    const Coords startCoords = battleMap.getCombatantCoordinates(_target);
    const int startDist = battleMap.getHopDistanceCombatants(_target, *caster);

    // All cells reachable within the target's full Speed, plus their movement cost.
    const DijkstraResult dijkstra = battleMap.calcDijkstra(_target);
    const int N = static_cast<int>(battleMap.getGridSize());

    std::optional<Coord> bestCell;
    int bestDistFromCaster = startDist;
    double bestThreat = std::numeric_limits<double>::max();

    for(int x = 0; x < N; ++x)
      {
        for(int y = 0; y < N; ++y)
          {
            const int cost = dijkstra.dist[x * N + y];
            if(cost <= 0 || cost > speed)
              {
                continue; // unreachable, current cell, or beyond movement
              }
            Coord cell{x, y};
            Coords candidate(cell, _target.getSize());
            if(!candidate.areValidCoords(battleMap.getGridSize()) || !battleMap.areEmptyOrSelf(candidate, _target))
              {
                continue;
              }
            int distFromCaster = getHopDistanceCoords(candidate, casterCoords);
            if(distFromCaster < bestDistFromCaster)
              {
                continue; // must end up at least as far away as it started
              }
            // The target plans the safest route, so among the farthest cells pick the lowest incoming threat.
            double threat = std::numeric_limits<double>::max();
            battleMap.withCombatantPosition(&_target, cell,
                                            [&] { threat = calculateAvgThreatIn(&_target, 2, static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE)); });
            if(distFromCaster > bestDistFromCaster || (distFromCaster == bestDistFromCaster && threat < bestThreat))
              {
                bestDistFromCaster = distFromCaster;
                bestThreat = threat;
                bestCell = cell;
              }
          }
      }

    if(bestCell)
      {
        battleMap.moveCombatant(_target, *bestCell, true);
      }
  }
}
