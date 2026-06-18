#include "spells/cloud_of_daggers.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include <memory>

namespace enc
{

  CloudOfDaggersFactory::CloudOfDaggersFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("CloudOfDaggersFactory", "Cloud of Daggers", caster, abilityType), _abilityType(abilityType), _resource(resource),
        _dmgDice({4, 4})
  {}

  std::vector<std::shared_ptr<Actoid>> CloudOfDaggersFactory::createAll(void *previousActionInDag)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
      = battleMap.findBestPlacementHarmfulSquare(_combatant, static_cast<int>(CloudOfDaggersFactory::range), 1);
    return {std::make_shared<CloudOfDaggers>(coord, *this)};
  }

  std::shared_ptr<Actoid> CloudOfDaggersFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<CloudOfDaggers>(*coord, *this);
  }

  double CloudOfDaggersFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const { return avgRoll(_dmgDice); }

  double CloudOfDaggersFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    return 0.0; // No need
  }

  double CloudOfDaggersFactory::calculateMaxThreat() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
      = battleMap.findBestPlacementHarmfulSquare(_combatant, static_cast<int>(CloudOfDaggersFactory::range), 1);
    return CloudOfDaggers(coord, *this).calculateThreat(Kwargs());
  }

  std::string CloudOfDaggers::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    return prefix + "Cloud of Daggers at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string CloudOfDaggers::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_CLOUD_OF_DAGGERS) ? "Quickened " : "";
    return prefix + "Cloud of Daggers";
  }

  double CloudOfDaggers::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();

    std::vector<Combatant *> affectedCombatants = battleMap.getCombatantsAffectedByBoxAoE(CloudOfDaggersFactory::target, _coord);

    double acc = 0.0;
    for(auto *aff : affectedCombatants)
      {
        double avgDmg = avgRoll(_factory._dmgDice);
        acc += (teams.areEnemies(*_factory._combatant, *aff) ? 1.0 : -3.0) * avgDmg;
      }
    return acc;
  }

  double CloudOfDaggers::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return 0.0; // Not relevant for this ability
  }

  std::optional<CoordVector>
  CloudOfDaggers::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    Combatant *swallower = _factory._combatant->getSwallower();
    if(swallower)
      {
        return std::nullopt;
      }

    BattleMap &battleMap = BattleMap::getInstance();
    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_coord), distances, _factory._combatant->getSize(),
                                                       static_cast<int>(CloudOfDaggersFactory::range), _factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*_factory._combatant), Coords(_coord))
            <= static_cast<int>(CloudOfDaggersFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }

    return std::nullopt;
  }

  void CloudOfDaggers::activate(const Kwargs &kwargs)
  {
    _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
  }

  void CloudOfDaggers::deactivate() { _factory._combatant->breakConcentration(); }

  bool CloudOfDaggers::deactivateForCombatant(Combatant *combatant)
  {
    assert(false);
    return false;
  }

  void CloudOfDaggers::onEnter(Combatant *combatant)
  {
    int damage = rollDice(_factory._dmgDice);
    combatant->receiveDmg(damage, CloudOfDaggersFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void CloudOfDaggers::onMoveWithin(Combatant * /*combatant*/) {}

  void CloudOfDaggers::onExit(Combatant * /*combatant*/) {}

  void CloudOfDaggers::onStartOfTurn(Combatant *combatant)
  {
    int damage = rollDice(_factory._dmgDice);
    combatant->receiveDmg(damage, CloudOfDaggersFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void CloudOfDaggers::onEndOfTurn(Combatant * /*combatant*/) {}

  double CloudOfDaggers::threatOnEnter(Combatant * /*target*/, const Kwargs & /*kwargs*/) const
  {
    return avgRoll(_factory._dmgDice);
  }

  double CloudOfDaggers::threatOnStartOfTurn(Combatant * /*target*/, const Kwargs & /*kwargs*/) const
  {
    return avgRoll(_factory._dmgDice);
  }

  double CloudOfDaggers::threatOnMoveWithin(Combatant * /*target*/, const Kwargs & /*kwargs*/) const { return 0.0; }

  double CloudOfDaggers::threatOnEndOfTurn(Combatant * /*target*/, const Kwargs & /*kwargs*/) const { return 0.0; }
} // namespace enc
