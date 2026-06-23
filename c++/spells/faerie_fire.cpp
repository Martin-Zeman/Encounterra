#include "spells/faerie_fire.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include "core/threat_utils.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <memory>

namespace enc
{

  FaerieFireFactory::FaerieFireFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("FaerieFireFactory", "Faerie Fire", caster, abilityType), _dc(dc), _resource(resource), _savingThrow(SavingThrow::DEX)
  {}

  Coord FaerieFireFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
        = battleMap.findBestPlacementHarmfulSquare(_combatant, static_cast<int>(FaerieFireFactory::range), TRANSLATE_BOX.at(FaerieFireFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> FaerieFireFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_shared<FaerieFire>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> FaerieFireFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<FaerieFire>(*coord, *this);
  }

  double FaerieFireFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target)
       <= static_cast<double>(static_cast<int>(FaerieFireFactory::range) + TRANSLATE_BOX.at(FaerieFireFactory::target)))
      {
        return getSavingThrowFailProb(_dc, target->getSavingThrows().at(_savingThrow)) * FaerieFireFactory::THREAT_PER_TARGET;
      }
    return 0;
  }

  double FaerieFireFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double FaerieFireFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return FaerieFire(bestCoord, *this).calculateThreat(Kwargs());
  }

  std::string FaerieFire::toString() const
  {
    return "Faerie Fire at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string FaerieFire::shorthandStr() const { return "Faerie Fire"; }

  double FaerieFire::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affectedCombatants = battleMap.getCombatantsAffectedByBoxAoE(FaerieFireFactory::target, _coord);
    double acc = 0.0;
    for(auto aff : affectedCombatants)
      {
        double benefit = getSavingThrowFailProb(_factory._dc, aff->getSavingThrows().at(_factory._savingThrow)) * FaerieFireFactory::THREAT_PER_TARGET;
        acc += (teams.areEnemies(*_factory._combatant, *aff) ? 1.0 : -3.0) * benefit;
      }
    return acc;
  }

  double FaerieFire::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  void FaerieFire::activate(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> potentiallyAffected = battleMap.getCombatantsAffectedByBoxAoE(FaerieFireFactory::target, _coord);
    bool anyFailed = false;
    for(auto *pac : potentiallyAffected)
      {
        if(!rollSavingThrow(pac->getSavingThrows().at(_factory._savingThrow), _factory._dc, RollType::STRAIGHT))
          {
            anyFailed = true;
            // The creature is outlined in light: it loses any current Invisible condition and can't benefit from
            // the Invisible condition for the duration.
            pac->removeCondition(Conditions::INVISIBLE);
            if(!pac->isAffectedBy(Conditions::CANNOT_TURN_INVISIBLE))
              {
                pac->applyCondition(Condition(Conditions::CANNOT_TURN_INVISIBLE, _factory._combatant, this, pac));
              }
            _combatants.push_back(pac);
          }
      }
    if(anyFailed)
      {
        _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
      }
  }

  void FaerieFire::deactivate()
  {
    for(auto *aff : _combatants)
      {
        aff->removeCondition(Conditions::CANNOT_TURN_INVISIBLE, _factory._combatant);
      }
    _factory._combatant->breakConcentration();
    _combatants.clear();
  }

  bool FaerieFire::deactivateForCombatant(Combatant *combatant)
  {
    if(std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end())
      {
        combatant->removeCondition(Conditions::CANNOT_TURN_INVISIBLE, _factory._combatant);
      }
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    return _combatants.empty();
  }

  bool FaerieFire::isAffecting(Combatant *combatant) const
  {
    return std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end();
  }

  void FaerieFire::onEnter(Combatant *combatant) { /* NOP */ }
  void FaerieFire::onMoveWithin(Combatant *combatant) { /* NOP */ }
  void FaerieFire::onExit(Combatant *combatant) { /* NOP */ }
  void FaerieFire::onStartOfTurn(Combatant *combatant) { /* NOP */ }
  void FaerieFire::onEndOfTurn(Combatant *combatant) { /* NOP */ }

  std::optional<CoordVector>
  FaerieFire::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
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
                                                       static_cast<int>(FaerieFireFactory::range), _factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*_factory._combatant), Coords(_coord))
            <= static_cast<int>(FaerieFireFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }
    return std::nullopt;
  }
}
