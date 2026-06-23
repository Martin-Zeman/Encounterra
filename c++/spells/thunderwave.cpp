#include "spells/thunderwave.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include <memory>

namespace enc
{

  ThunderwaveFactory::ThunderwaveFactory(int dc, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("ThunderwaveFactory", "Thunderwave", caster, abilityType), _dc(dc), _resource(resource), _savingThrow(SavingThrow::CON),
        _dmgDice({{2, 8}})
  {}

  Coord ThunderwaveFactory::findBestArgs() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants]
        = battleMap.findBestPlacementHarmfulSquare(_combatant, static_cast<int>(ThunderwaveFactory::range), TRANSLATE_BOX.at(ThunderwaveFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> ThunderwaveFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_shared<Thunderwave>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> ThunderwaveFactory::create(void *target)
  {
    Coord *coord = static_cast<Coord *>(target);
    return std::make_shared<Thunderwave>(*coord, *this);
  }

  double ThunderwaveFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target)
       <= static_cast<double>(static_cast<int>(ThunderwaveFactory::range) + TRANSLATE_BOX.at(ThunderwaveFactory::target)))
      {
        return std::min(static_cast<double>(target->getCurrentHp()),
                        meanDmgDcAttack(_dc, _dmgDice, true, target->getSavingThrows().at(_savingThrow), target->isImmuneTo(ThunderwaveFactory::dmgType),
                                        target->isResistantTo(ThunderwaveFactory::dmgType)));
      }
    return 0;
  }

  double ThunderwaveFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0; }

  double ThunderwaveFactory::calculateMaxThreat() const
  {
    auto bestCoord = findBestArgs();
    return Thunderwave(bestCoord, *this).calculateThreat(Kwargs());
  }

  std::string Thunderwave::toString() const
  {
    return "Thunderwave at (" + std::to_string(_coord[0]) + ", " + std::to_string(_coord[1]) + ")";
  }

  std::string Thunderwave::shorthandStr() const { return "Thunderwave"; }

  double Thunderwave::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    const ThunderwaveFactory &factory = dynamic_cast<const ThunderwaveFactory &>(getFactory());
    std::vector<Combatant *> affectedCombatants = battleMap.getCombatantsAffectedByBoxAoE(ThunderwaveFactory::target, _coord);
    double acc = 0.0;
    for(auto aff : affectedCombatants)
      {
        double avgDmg = std::min(static_cast<double>(aff->getCurrentHp()),
                                 meanDmgDcAttack(factory._dc, factory._dmgDice, true, aff->getSavingThrows().at(factory._savingThrow),
                                                 aff->isImmuneTo(ThunderwaveFactory::dmgType), aff->isResistantTo(ThunderwaveFactory::dmgType)));
        acc += (teams.areEnemies(*factory._combatant, *aff) ? 1.0 : -3.0) * avgDmg;
      }
    return acc;
  }

  double Thunderwave::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0; }

  std::optional<CoordVector>
  Thunderwave::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    ThunderwaveFactory &factory = dynamic_cast<ThunderwaveFactory &>(getFactory());
    Combatant *swallower = factory._combatant->getSwallower();
    if(swallower)
      {
        return {};
      }
    BattleMap &battleMap = BattleMap::getInstance();
    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_coord), distances, factory._combatant->getSize(),
                                                       static_cast<int>(ThunderwaveFactory::range), factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*factory._combatant), Coords(_coord))
            <= static_cast<int>(ThunderwaveFactory::range))
      {
        CoordVector coords = {battleMap.getCombatantCoordinates(*factory._combatant).getRoot()};
        return coords;
      }
    return {};
  }
}
