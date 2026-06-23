#include "spells/moonbeam.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include <memory>

namespace enc
{

  MoonbeamFactory::MoonbeamFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("MoonbeamFactory", "Moonbeam", caster, abilityType), _dc(dc), _resource(resource), _savingThrow(SavingThrow::CON),
        _dmgDice({{2, 10}})
  {}

  Coord MoonbeamFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
        = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(MoonbeamFactory::range), TRANSLATE_RADIUS.at(MoonbeamFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> MoonbeamFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_shared<Moonbeam>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> MoonbeamFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<Moonbeam>(*coord, *this);
  }

  double MoonbeamFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, _dmgDice, true, target->getSavingThrows().at(_savingThrow), target->isImmuneTo(MoonbeamFactory::dmgType),
                                    target->isResistantTo(MoonbeamFactory::dmgType)));
  }

  double MoonbeamFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double MoonbeamFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return Moonbeam(bestCoord, *this).calculateThreat(Kwargs());
  }

  std::string Moonbeam::toString() const { return "Moonbeam at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")"; }

  std::string Moonbeam::shorthandStr() const { return "Moonbeam"; }

  double Moonbeam::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affectedCombatants
        = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, MoonbeamFactory::target, SpellType::HARMFUL, _coord);
    double acc = 0.0;
    for(auto *aff : affectedCombatants)
      {
        double avgDmg = std::min(static_cast<double>(aff->getCurrentHp()),
                                 meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, aff->getSavingThrows().at(_factory._savingThrow),
                                                 aff->isImmuneTo(MoonbeamFactory::dmgType), aff->isResistantTo(MoonbeamFactory::dmgType)));
        acc += (teams.areEnemies(*_factory._combatant, *aff) ? 1.0 : -3.0) * avgDmg;
      }
    return acc;
  }

  double Moonbeam::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  std::optional<CoordVector>
  Moonbeam::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
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
                                                       static_cast<int>(MoonbeamFactory::range), _factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*_factory._combatant), Coords(_coord))
            <= static_cast<int>(MoonbeamFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }
    return std::nullopt;
  }

  void Moonbeam::activate(const Kwargs &kwargs) { _factory._combatant->setConcentrationEffect(Effect::shared_from_this()); }

  void Moonbeam::deactivate() { _factory._combatant->breakConcentration(); }

  bool Moonbeam::deactivateForCombatant(Combatant *combatant) { return false; }

  void Moonbeam::applyMoonlight(Combatant *combatant)
  {
    int dmg = rollDiceMulti(_factory._dmgDice);
    bool saved = rollSavingThrow(combatant->getSavingThrows().at(_factory._savingThrow), _factory._dc, RollType::STRAIGHT);
    if(saved)
      {
        dmg /= 2;
      }
    combatant->receiveDmg(dmg, MoonbeamFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void Moonbeam::onEnter(Combatant *combatant) { applyMoonlight(combatant); }
  void Moonbeam::onStartOfTurn(Combatant *combatant) { applyMoonlight(combatant); }
  void Moonbeam::onMoveWithin(Combatant *combatant) { /*NOP*/ }
  void Moonbeam::onExit(Combatant *combatant) { /*NOP*/ }
  void Moonbeam::onEndOfTurn(Combatant *combatant) { /*NOP*/ }

  double Moonbeam::threatOnEnter(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, target->getSavingThrows().at(_factory._savingThrow),
                                    target->isImmuneTo(MoonbeamFactory::dmgType), target->isResistantTo(MoonbeamFactory::dmgType)));
  }

  double Moonbeam::threatOnStartOfTurn(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, target->getSavingThrows().at(_factory._savingThrow),
                                    target->isImmuneTo(MoonbeamFactory::dmgType), target->isResistantTo(MoonbeamFactory::dmgType)));
  }
}
