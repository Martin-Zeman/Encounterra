#include "spells/color_spray.hpp"
#include "core/battle_map.hpp"
#include "core/combatant.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/threat_utils.hpp"
#include "effects/effect_tracker.hpp"
#include <algorithm>
#include <iostream>
#include <memory>

namespace enc
{
  ColorSprayFactory::ColorSprayFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("ColorSprayFactory", "Color Spray", caster, abilityType), _dc(dc), _resource(resource)
  {}

  std::vector<std::shared_ptr<Actoid>> ColorSprayFactory::createAll(void *previousActionInDag)
  {
    Coord origin = BattleMap::getInstance().getCombatantCoordinates(*_combatant).getRoot();
    return {std::make_shared<ColorSpray>(origin, *this)};
  }

  std::shared_ptr<Actoid> ColorSprayFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<ColorSpray>(*coord, *this);
  }

  double ColorSprayFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    return getSavingThrowFailProb(_dc, target->getSavingThrow(ColorSprayFactory::savingThrow)) * ColorSprayFactory::THREAT_PER_TARGET;
  }

  double ColorSprayFactory::calculateMaxThreat() const
  {
    Coord origin = BattleMap::getInstance().getCombatantCoordinates(*_combatant).getRoot();
    return ColorSpray(origin, *this).calculateThreat(Kwargs());
  }

  std::string ColorSpray::toString() const
  {
    return "Color Spray at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string ColorSpray::shorthandStr() const { return "Color Spray"; }

  double ColorSpray::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    std::vector<Combatant *> affected
        = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, ColorSprayFactory::target, ColorSprayFactory::type, _coord);
    double acc = 0.0;
    for(auto *aff : affected)
      {
        double benefit = _factory.calculateThreatToTarget(aff, kwargs);
        // A creature charmed by our side is friendly: hitting it counts as friendly fire, like striking an ally.
        bool friendly = !teams.areEnemies(*_factory._combatant, *aff) || isCharmedByTeamOf(_factory._combatant, aff);
        acc += (friendly ? -3.0 : 1.0) * benefit;
      }
    return acc;
  }

  void ColorSpray::activate(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> potentiallyAffected
        = battleMap.getCombatantsAffectedBySphereAoE(_factory._combatant, ColorSprayFactory::target, ColorSprayFactory::type, _coord);
    Teams &teams = Teams::getInstance();
    for(auto *pac : potentiallyAffected)
      {
        if(!teams.areEnemies(*_factory._combatant, *pac))
          {
            continue;
          }
        if(!rollSavingThrow(pac->getSavingThrow(ColorSprayFactory::savingThrow), _factory._dc, RollType::STRAIGHT))
          {
            pac->applyCondition(Condition(Conditions::BLINDED, _factory._combatant, this, pac));
            _combatants.push_back(pac);
            std::cout << pac->_name << " failed the save and is blinded by Color Spray." << std::endl;
          }
          else
          {
            std::cout << pac->_name << " saved against Color Spray." << std::endl;
          }
      }
  }

  void ColorSpray::deactivate()
  {
    for(auto *aff : _combatants)
      {
        aff->removeCondition(Conditions::BLINDED, _factory._combatant);
      }
    _combatants.clear();
  }

  bool ColorSpray::deactivateForCombatant(Combatant *combatant)
  {
    if(std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end())
      {
        combatant->removeCondition(Conditions::BLINDED, _factory._combatant);
      }
    _combatants.erase(std::remove(_combatants.begin(), _combatants.end(), combatant), _combatants.end());
    return !_combatants.empty();
  }

  bool ColorSpray::isAffecting(Combatant *combatant) const
  {
    return std::find(_combatants.begin(), _combatants.end(), combatant) != _combatants.end();
  }

  void ColorSpray::onEnter(Combatant *combatant) { /* NOP */ }
  void ColorSpray::onMoveWithin(Combatant *combatant) { /* NOP */ }
  void ColorSpray::onExit(Combatant *combatant) { /* NOP */ }
  void ColorSpray::onStartOfTurn(Combatant *combatant) { /* NOP */ }
  void ColorSpray::onEndOfTurn(Combatant *combatant) { /* NOP */ }

  std::optional<CoordVector> ColorSpray::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }
    return CoordVector{BattleMap::getInstance().getCombatantCoordinates(*_factory._combatant).getRoot()};
  }
}
