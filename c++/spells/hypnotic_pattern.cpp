#include "spells/hypnotic_pattern.hpp"
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
  HypnoticPatternFactory::HypnoticPatternFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("HypnoticPatternFactory", "Hypnotic Pattern", caster, abilityType), _dc(dc), _resource(resource)
  {}

  Coord HypnoticPatternFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants] = battleMap.findBestPlacementHarmfulSquare(
        _combatant, static_cast<int>(HypnoticPatternFactory::range), TRANSLATE_BOX.at(HypnoticPatternFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> HypnoticPatternFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_shared<HypnoticPattern>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> HypnoticPatternFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<HypnoticPattern>(*coord, *this);
  }

  double HypnoticPatternFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // A creature immune to the Charmed condition is unaffected by Hypnotic Pattern.
    if(target->isImmuneToCondition(Conditions::CHARMED))
      {
        return 0;
      }
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target)
       <= static_cast<double>(static_cast<int>(HypnoticPatternFactory::range) + TRANSLATE_BOX.at(HypnoticPatternFactory::target)))
      {
        return getSavingThrowFailProb(_dc, target->getSavingThrows().at(HypnoticPatternFactory::savingThrow)) * HypnoticPatternFactory::THREAT_PER_TARGET;
      }
    return 0;
  }

  double HypnoticPatternFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double HypnoticPatternFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return HypnoticPattern(bestCoord, *this).calculateThreat(Kwargs());
  }

  std::string HypnoticPattern::toString() const
  {
    return "Hypnotic Pattern at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string HypnoticPattern::shorthandStr() const { return "Hypnotic Pattern"; }

  double HypnoticPattern::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affectedCombatants = battleMap.getCombatantsAffectedByBoxAoE(HypnoticPatternFactory::target, _coord);
    double acc = 0.0;
    for(auto aff : affectedCombatants)
      {
        // A creature immune to the Charmed condition is unaffected, so it contributes no threat either way.
        if(aff->isImmuneToCondition(Conditions::CHARMED))
          {
            continue;
          }
        double benefit
            = getSavingThrowFailProb(_factory._dc, aff->getSavingThrows().at(HypnoticPatternFactory::savingThrow)) * HypnoticPatternFactory::THREAT_PER_TARGET;
        // Charming an enemy is good; catching an ally (or a creature charmed onto our side) is bad.
        bool friendly = !teams.areEnemies(*_factory._combatant, *aff) || isCharmedByTeamOf(_factory._combatant, aff);
        acc += (friendly ? -3.0 : 1.0) * benefit;
      }
    return acc;
  }

  double HypnoticPattern::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  void HypnoticPattern::activate(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> potentiallyAffected = battleMap.getCombatantsAffectedByBoxAoE(HypnoticPatternFactory::target, _coord);
    bool anyFailed = false;
    for(auto *pac : potentiallyAffected)
      {
        // A creature immune to the Charmed condition, or already removed from the fight, is unaffected.
        if(pac->isImmuneToCondition(Conditions::CHARMED) || pac->isAffectedByAny({Conditions::INCAPACITATED, Conditions::UNCONSCIOUS}))
          {
            continue;
          }
        bool saved = rollSavingThrow(pac->getSavingThrow(HypnoticPatternFactory::savingThrow), _factory._dc,
                                     reconcileRollTypes(pac->getSavingThrowRollTypeMods(HypnoticPatternFactory::savingThrow)));
        if(!saved)
          {
            // Charmed + Incapacitated (Speed 0). Flagged AWAKENED_BY_DMG so taking damage ends the effect.
            pac->applyCondition(Condition(Conditions::CHARMED | Conditions::INCAPACITATED | Conditions::AWAKENED_BY_DMG, _factory._combatant, this));
            _combatants.push_back(pac);
            std::cout << pac->_name << " is Charmed and Incapacitated by Hypnotic Pattern." << std::endl;
          }
        else
          {
            std::cout << pac->_name << " saved against Hypnotic Pattern." << std::endl;
          }
      }
    if(!_combatants.empty())
      {
        anyFailed = true;
        _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
      }
    (void)anyFailed;
  }

  void HypnoticPattern::removeHypnoticConditions(Combatant *combatant) const
  {
    combatant->removeCondition(Conditions::CHARMED, _factory._combatant);
    combatant->removeCondition(Conditions::INCAPACITATED, _factory._combatant);
    combatant->removeCondition(Conditions::AWAKENED_BY_DMG, _factory._combatant);
  }

  void HypnoticPattern::deactivate()
  {
    for(auto *aff : _combatants)
      {
        removeHypnoticConditions(aff);
      }
    _factory._combatant->breakConcentration();
    _combatants.clear();
  }

  bool HypnoticPattern::deactivateForCombatant(Combatant *combatant)
  {
    if(std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end())
      {
        removeHypnoticConditions(combatant);
        std::cout << combatant->_name << " snaps out of Hypnotic Pattern." << std::endl;
      }
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    if(_combatants.empty())
      {
        _factory._combatant->breakConcentration();
        return false;
      }
    return true;
  }

  bool HypnoticPattern::isAffecting(Combatant *combatant) const
  {
    return std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end();
  }

  void HypnoticPattern::onEnter(Combatant *combatant) { /* NOP: only creatures present when cast must save. */ }
  void HypnoticPattern::onMoveWithin(Combatant *combatant) { /* NOP */ }
  void HypnoticPattern::onExit(Combatant *combatant) { /* NOP: leaving the area does not end the charm. */ }
  void HypnoticPattern::onStartOfTurn(Combatant *combatant) { /* NOP */ }
  void HypnoticPattern::onEndOfTurn(Combatant *combatant) { /* NOP */ }

  std::optional<CoordVector>
  HypnoticPattern::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
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
                                                       static_cast<int>(HypnoticPatternFactory::range), _factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*_factory._combatant), Coords(_coord))
            <= static_cast<int>(HypnoticPatternFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }
    return std::nullopt;
  }
}
