#include "spells/flaming_sphere.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include "core/combatant.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <memory>

namespace enc
{
  // ---------------------------------------------------------------------------
  // FlamingSphereFactory
  // ---------------------------------------------------------------------------

  FlamingSphereFactory::FlamingSphereFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("FlamingSphereFactory", "Flaming Sphere", caster, abilityType), _dc(dc), _resource(resource),
        _savingThrow(SavingThrow::DEX), _dmgDice({{2, 6}})
  {}

  Coord FlamingSphereFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
        = battleMap.findBestPlacementHarmfulSquare(_combatant, static_cast<int>(FlamingSphereFactory::range), TRANSLATE_BOX.at(FlamingSphereFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> FlamingSphereFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_shared<FlamingSphere>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> FlamingSphereFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<FlamingSphere>(*coord, *this);
  }

  double FlamingSphereFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target)
       <= static_cast<double>(static_cast<int>(FlamingSphereFactory::range) + TRANSLATE_BOX.at(FlamingSphereFactory::target)))
      {
        return std::min(static_cast<double>(target->getCurrentHp()),
                        meanDmgDcAttack(_dc, _dmgDice, true, target->getSavingThrows().at(_savingThrow),
                                        target->isImmuneTo(FlamingSphereFactory::dmgType), target->isResistantTo(FlamingSphereFactory::dmgType)));
      }
    return 0;
  }

  double FlamingSphereFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double FlamingSphereFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return FlamingSphere(bestCoord, *this).calculateThreat(Kwargs());
  }

  // ---------------------------------------------------------------------------
  // FlamingSphere
  // ---------------------------------------------------------------------------

  std::string FlamingSphere::toString() const
  {
    return "Flaming Sphere at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string FlamingSphere::shorthandStr() const { return "Flaming Sphere"; }

  void FlamingSphere::moveOrigin(const Coord &coord)
  {
    _coord = coord;
    _origin = coord;
    _affectedCoords = getCoordsAffectedBySquareAoE(_origin, _length, BattleMap::getInstance().getGridSize());
  }

  double FlamingSphere::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> enemies = battleMap.getNonSwallowedEnemiesWithinRadius(_factory._combatant, static_cast<int>(FlamingSphereFactory::range));
    if(enemies.empty())
      {
        return 0;
      }
    double acc = 0.0;
    for(auto *enemy : enemies)
      {
        acc += std::min(static_cast<double>(enemy->getCurrentHp()),
                        meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, enemy->getSavingThrows().at(_factory._savingThrow),
                                        enemy->isImmuneTo(FlamingSphereFactory::dmgType), enemy->isResistantTo(FlamingSphereFactory::dmgType)));
      }
    return acc / static_cast<double>(enemies.size());
  }

  double FlamingSphere::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  std::optional<CoordVector>
  FlamingSphere::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
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
                                                       static_cast<int>(FlamingSphereFactory::range), _factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*_factory._combatant), Coords(_coord))
            <= static_cast<int>(FlamingSphereFactory::range))
      {
        return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
      }
    return std::nullopt;
  }

  void FlamingSphere::activate(const Kwargs &kwargs)
  {
    _factory._combatant->setConcentrationEffect(Effect::shared_from_this());
    enable();
  }

  void FlamingSphere::deactivate()
  {
    _factory._combatant->breakConcentration();
    disable();
  }

  bool FlamingSphere::deactivateForCombatant(Combatant *combatant) { return false; }

  bool FlamingSphere::isAffecting(Combatant *combatant) const { return false; }

  void FlamingSphere::enable()
  {
    auto ramFactory = std::make_shared<FlamingSphereRamFactory>(_factory._combatant, _factory._dc, this);
    _factory._combatant->getBonusActionFactories().emplace_back(ramFactory);
  }

  void FlamingSphere::disable()
  {
    auto &bonusFactories = _factory._combatant->getBonusActionFactories();
    bonusFactories.erase(std::remove_if(bonusFactories.begin(), bonusFactories.end(),
                                        [](const std::shared_ptr<ActoidFactory> &factory)
                                        { return factory->getAbilityType() == AbilityType::FLAMING_SPHERE_RAM; }),
                         bonusFactories.end());
  }

  void FlamingSphere::onEnter(Combatant *combatant)
  {
    int damage = rollDiceMulti(_factory._dmgDice);
    combatant->receiveDmg(damage, FlamingSphereFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void FlamingSphere::onEndOfTurn(Combatant *combatant)
  {
    int damage = rollDiceMulti(_factory._dmgDice);
    combatant->receiveDmg(damage, FlamingSphereFactory::dmgType);
    BattleMap::getInstance().removeCombatantIfDead(*combatant);
  }

  void FlamingSphere::onMoveWithin(Combatant *combatant) { /*NOP*/ }
  void FlamingSphere::onExit(Combatant *combatant) { /*NOP*/ }
  void FlamingSphere::onStartOfTurn(Combatant *combatant) { /*NOP*/ }

  double FlamingSphere::threatOnEnter(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, target->getSavingThrows().at(_factory._savingThrow),
                                    target->isImmuneTo(FlamingSphereFactory::dmgType), target->isResistantTo(FlamingSphereFactory::dmgType)));
  }

  double FlamingSphere::threatOnEndOfTurn(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_factory._dc, _factory._dmgDice, true, target->getSavingThrows().at(_factory._savingThrow),
                                    target->isImmuneTo(FlamingSphereFactory::dmgType), target->isResistantTo(FlamingSphereFactory::dmgType)));
  }

  // ---------------------------------------------------------------------------
  // FlamingSphereRamFactory
  // ---------------------------------------------------------------------------

  FlamingSphereRamFactory::FlamingSphereRamFactory(Combatant *caster, int dc, FlamingSphere *actionEnablerEffect)
      : DirectThreatFactory("FlamingSphereRamFactory", "Flaming Sphere Ram", caster, AbilityType::FLAMING_SPHERE_RAM), _dc(dc),
        _actionEnablerEffect(actionEnablerEffect), _savingThrow(SavingThrow::DEX), _dmgDice({{2, 6}})
  {
    setFlag(FactoryFlags::TRANSITIONS_TO_WILDSHAPE);
  }

  std::vector<std::shared_ptr<Actoid>> FlamingSphereRamFactory::createAll(void *previousActionInDag)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<std::shared_ptr<Actoid>> result;
    for(auto *enemy : battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, FlamingSphereRamFactory::RANGE))
      {
        Coord coord = battleMap.getCombatantCoordinates(*enemy).getRoot();
        result.emplace_back(std::make_shared<FlamingSphereRam>(enemy, coord, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> FlamingSphereRamFactory::create(void *target)
  {
    Combatant *enemy = static_cast<Combatant *>(target);
    Coord coord = BattleMap::getInstance().getCombatantCoordinates(*enemy).getRoot();
    return std::make_shared<FlamingSphereRam>(enemy, coord, *this);
  }

  double FlamingSphereRamFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    return std::min(static_cast<double>(target->getCurrentHp()),
                    meanDmgDcAttack(_dc, _dmgDice, true, target->getSavingThrows().at(_savingThrow),
                                    target->isImmuneTo(FlamingSphereRamFactory::dmgType), target->isResistantTo(FlamingSphereRamFactory::dmgType)));
  }

  double FlamingSphereRamFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double FlamingSphereRamFactory::calculateMaxThreat() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    double best = 0.0;
    for(auto *enemy : battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, FlamingSphereRamFactory::RANGE))
      {
        best = std::max(best, calculateThreatToTarget(enemy, Kwargs()));
      }
    return best;
  }

  // ---------------------------------------------------------------------------
  // FlamingSphereRam
  // ---------------------------------------------------------------------------

  std::string FlamingSphereRam::toString() const { return "Flaming Sphere Ram into " + _target->_name; }

  std::string FlamingSphereRam::shorthandStr() const { return "Flaming Sphere Ram"; }

  double FlamingSphereRam::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(_target, kwargs); }

  double FlamingSphereRam::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  std::optional<CoordVector>
  FlamingSphereRam::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    return CoordVector{battleMap.getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
