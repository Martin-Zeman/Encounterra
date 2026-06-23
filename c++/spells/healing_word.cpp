#include "spells/healing_word.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <algorithm>
#include <limits>

namespace enc
{

  HealingWordFactory::HealingWordFactory(Combatant *caster, Resource *resource, int mod, AbilityType abilityType, Die healDice)
      : DirectThreatFactory("HealingWordFactory", "Healing Word", caster, abilityType), _resource(resource), _mod(mod), _healDice(healDice)
  {}

  std::vector<Combatant *> HealingWordFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(_combatant->getSwallower())
      {
        return {};
      }
    std::vector<Combatant *> targets = battleMap.getNonSwallowedAlliesWithinRadius(_combatant, static_cast<int>(HealingWordFactory::range));
    targets.push_back(_combatant);
    return targets;
  }

  std::vector<std::shared_ptr<Actoid>> HealingWordFactory::createAll(void *previousActionInDag)
  {
    auto targets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(targets.size());
    for(const auto &t : targets)
      {
        result.push_back(std::make_shared<HealingWord>(*t, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> HealingWordFactory::create(void *target)
  {
    return std::make_shared<HealingWord>(*static_cast<Combatant *>(target), *this);
  }

  double HealingWordFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower())
      {
        return 0.0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(HealingWordFactory::range))
      {
        int missingHp = target->getMaxHp() - target->getCurrentHp();
        return std::min(static_cast<double>(missingHp), avgRoll(_healDice) + _mod);
      }
    return 0.0;
  }

  double HealingWordFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const { return 0.0; }

  double HealingWordFactory::calculateMaxThreat() const { return avgRoll(_healDice) + _mod; }

  std::string HealingWord::toString() const { return shorthandStr() + " on " + _target._name; }

  std::string HealingWord::shorthandStr() const { return "Healing Word"; }

  double HealingWord::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double HealingWord::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector>
  HealingWord::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(_factory._combatant->getSwallower())
      {
        return std::nullopt;
      }
    Coord currCoord = battleMap.getCombatantCoordinates(*_factory._combatant).getRoot();
    if(!_factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, _factory._combatant->getSize(),
                                                       static_cast<int>(HealingWordFactory::range), _factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*_factory._combatant, _target) <= static_cast<int>(HealingWordFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return std::nullopt;
  }
}
