#include "spells/magic_missile.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <algorithm>
#include <limits>

namespace enc
{
  MagicMissileFactory::MagicMissileFactory(AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("MagicMissileFactory", "Magic Missile", caster, abilityType), _resource(resource)
  {}

  std::vector<std::array<Combatant *, 3>> MagicMissileFactory::getEligibleTargetSets() const
  {
    if(auto *swallower = _combatant->getSwallower())
      {
        return {{{swallower, swallower, swallower}}};
      }

    BattleMap &battleMap = BattleMap::getInstance();
    std::vector<Combatant *> enemies = battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(MagicMissileFactory::range));
    std::vector<std::array<Combatant *, 3>> targetSets;
    for(size_t i = 0; i < enemies.size(); ++i)
      {
        for(size_t j = i; j < enemies.size(); ++j)
          {
            for(size_t k = j; k < enemies.size(); ++k)
              {
                targetSets.push_back({enemies[i], enemies[j], enemies[k]});
              }
          }
      }
    return targetSets;
  }

  std::vector<std::shared_ptr<Actoid>> MagicMissileFactory::createAll(void *previousActionInDag)
  {
    auto targetSets = getEligibleTargetSets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targetSets.size());
    for(const auto &targets : targetSets)
      {
        result.push_back(std::make_shared<MagicMissile>(targets, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> MagicMissileFactory::create(void *target)
  {
    return std::make_shared<MagicMissile>(*static_cast<std::array<Combatant *, 3> *>(target), *this);
  }

  double MagicMissileFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower() || battleMap.getCartesianDistanceCombatants(*_combatant, *target) > static_cast<int>(MagicMissileFactory::range))
      {
        return 0.0;
      }
    if(target->isImmuneTo(MagicMissileFactory::dmgType))
      {
        return 0.0;
      }
    double dartThreat = avgRoll(MagicMissileFactory::dmgDice) + MagicMissileFactory::dmgBonus;
    if(target->isResistantTo(MagicMissileFactory::dmgType))
      {
        dartThreat /= 2.0;
      }
    return std::min(static_cast<double>(target->getCurrentHp()), 3.0 * dartThreat);
  }

  double MagicMissileFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double MagicMissileFactory::calculateMaxThreat() const
  {
    double maxThreat = 0.0;
    for(const auto &targets : getEligibleTargetSets())
      {
        maxThreat = std::max(maxThreat, MagicMissile(targets, *this).calculateThreat({}));
      }
    return maxThreat;
  }

  std::string MagicMissile::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_MAGIC_MISSILE) ? "Quickened " : "";
    return prefix + "Magic Missile on " + _targets[0]->_name + ", " + _targets[1]->_name + ", and " + _targets[2]->_name;
  }

  std::string MagicMissile::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_MAGIC_MISSILE) ? "Quickened " : "";
    return prefix + "Magic Missile";
  }

  double MagicMissile::calculateThreat(const Kwargs &kwargs)
  {
    double threat = 0.0;
    for(auto *target : _targets)
      {
        if(target->isImmuneTo(MagicMissileFactory::dmgType))
          {
            continue;
          }
        double dartThreat = avgRoll(MagicMissileFactory::dmgDice) + MagicMissileFactory::dmgBonus;
        if(target->isResistantTo(MagicMissileFactory::dmgType))
          {
            dartThreat /= 2.0;
          }
        threat += dartThreat;
      }
    return threat;
  }

  double MagicMissile::calculateThreatDelta(const ThreatModifiers &modifiers) const { return 0.0; }

  std::optional<CoordVector>
  MagicMissile::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *caster = _factory._combatant;
    Coord currCoord = battleMap.getCombatantCoordinates(*caster).getRoot();
    if(caster->getSwallower())
      {
        return CoordVector{currCoord};
      }

    auto inRangeAtCurrent = [&]() {
      return std::all_of(_targets.begin(), _targets.end(), [&](Combatant *target) {
        return battleMap.getCartesianDistanceCombatants(*caster, *target) <= static_cast<int>(MagicMissileFactory::range);
      });
    };

    if(caster->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return inRangeAtCurrent() ? std::optional<CoordVector>(CoordVector{currCoord}) : std::nullopt;
      }

    CoordVector coords = battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*_targets[0]).get(), distances, caster->getSize(),
                                                                 static_cast<int>(MagicMissileFactory::range), caster->_instanceId);
    for(size_t i = 1; i < _targets.size(); ++i)
      {
        CoordVector targetCoords = battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(*_targets[i]).get(), distances,
                                                                           caster->getSize(), static_cast<int>(MagicMissileFactory::range),
                                                                           caster->_instanceId);
        coords.erase(std::remove_if(coords.begin(), coords.end(), [&targetCoords](const Coord &coord) {
                       return std::find(targetCoords.begin(), targetCoords.end(), coord) == targetCoords.end();
                     }),
                     coords.end());
      }
    return coords;
  }
}
