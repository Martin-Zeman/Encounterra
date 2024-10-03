#include "spells/fireball.hpp"
#include "core/battle_map.hpp"
#include "core/misc.hpp"
#include "core/teams.hpp"
#include "core/conditions.hpp"
#include "core/geometry.hpp"
#include <memory>

namespace enc
{

  Coord FireballFactory::findBestArgs() const
  {
    BattleMap & battleMap = BattleMap::getInstance();
    auto [coord, maxScore, affectedCombatants] = battleMap.findBestPlacementHarmfulCircular(_combatant, static_cast<int>(FireballFactory::range), TRANSLATE_RADIUS.at(FireballFactory::target));
    return coord;
  }

  std::vector<std::shared_ptr<Actoid>> FireballFactory::createAll(void *previousActionInDag)
  {
    auto bestCoord = findBestArgs();
    return {std::make_unique<Fireball>(bestCoord, *this)};
  }

  std::shared_ptr<Actoid> FireballFactory::create(void *target)
  {
    Coord* coord = static_cast<Coord*>(target);
    return std::make_shared<Fireball>(*coord, *this);
  }

  double FireballFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target)
       <= static_cast<double>(static_cast<int>(FireballFactory::range) + TRANSLATE_RADIUS.at(FireballFactory::target)))
      {
        return std::min(static_cast<double>(target->getCurrentHp()),
                        meanDmgDcAttack(_dc, _dmgDice, true, target->getSavingThrows().at(_savingThrow), target->isImmuneTo(FireballFactory::dmgType),
                                        target->isResistantTo(FireballFactory::dmgType)));
      }
    return 0;
  }

  double FireballFactory::calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/)
  {
    // No need for this ability
    return 0;
  }
  double FireballFactory::calculateMaxThreat()
  {
    auto bestCoord = findBestArgs();
    return Fireball(bestCoord, *this).calculateThreat(Kwargs());
  }

  double Fireball::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Teams &teams = Teams::getInstance();
    const FireballFactory &factory = dynamic_cast<const FireballFactory &>(getFactory());
    std::vector<Combatant *> affectedCombatants
      = battleMap.getCombatantsAffectedBySphereAoE(factory._combatant, FireballFactory::target, SpellType::HARMFUL, _coord);
    double acc = 0.0;
    for(auto aff : affectedCombatants)
      {
        double avgDmg = std::min(static_cast<double>(aff->getCurrentHp()),
                                 meanDmgDcAttack(factory._dc, factory._dmgDice, true, aff->getSavingThrows().at(factory._savingThrow),
                                                 aff->isImmuneTo(FireballFactory::dmgType), aff->isResistantTo(FireballFactory::dmgType)));
        acc += (teams.areEnemies(*factory._combatant, *aff) ? 1.0 : -3.0) * avgDmg;
      }
    return acc;
  }

  std::optional<std::vector<Coord>>
  Fireball::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    FireballFactory &factory = dynamic_cast<FireballFactory &>(getFactory());
    Combatant *swallower = factory._combatant->getSwallower();
    if(swallower)
      {
        return {};
      }
    BattleMap &battleMap = BattleMap::getInstance();
    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(Coords(_coord), distances, factory._combatant->getSize(),
                                                       static_cast<int>(FireballFactory::range), factory._combatant->_instanceId);
      }
    else if(getCartesianDistanceCoords(battleMap.getCombatantCoordinates(*factory._combatant), Coords(_coord))
            <= static_cast<int>(FireballFactory::range))
      {
        std::vector<Coord> coords = {battleMap.getCombatantCoordinates(*factory._combatant).get()[0]};
        return coords;
      }
    return {};
  }
}