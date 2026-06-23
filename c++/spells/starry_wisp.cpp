#include "spells/starry_wisp.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>

namespace enc
{

  StarryWispFactory::StarryWispFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("StarryWispFactory", "Starry Wisp", caster, abilityType), _toHit(toHit), _resource(resource),
        _dmgDice(StarryWispFactory::getDmgDice(caster->getLevel()))
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant *> StarryWispFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(StarryWispFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> StarryWispFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<StarryWisp>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> StarryWispFactory::create(void *target)
  {
    return std::make_shared<StarryWisp>(*static_cast<Combatant *>(target), *this);
  }

  double StarryWispFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = target->getSwallower();
    if(swallower)
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(StarryWispFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        return meanDmg(toHitTotal, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(StarryWispFactory::dmgType),
                       target->isResistantTo(StarryWispFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
      }
    return 0;
  }

  double StarryWispFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    if(target->isImmuneTo(StarryWispFactory::dmgType))
      {
        return 0;
      }

    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = targetAC + target->getAC();
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    int needToRollAtLeast = std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20));
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(needToRollAtLeast);
    double totalCrit = ROLL_TYPE_CRIT_DELTA.at(rollType);

    double modifiedThreat = meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC, target->isImmuneTo(StarryWispFactory::dmgType),
                                    target->isResistantTo(StarryWispFactory::dmgType), totalCrit);

    double originalThreat = meanDmg(_toHit, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(StarryWispFactory::dmgType),
                                    target->isResistantTo(StarryWispFactory::dmgType), 1);

    return modifiedThreat - originalThreat;
  }

  double StarryWispFactory::calculateMaxThreat() const
  {
    auto eligibleTargets = getEligibleTargets();
    double maxThreat = std::numeric_limits<double>::lowest();
    for(const auto &target : eligibleTargets)
      {
        double threat = StarryWisp(*target, *this).calculateThreat(Kwargs());
        maxThreat = std::max(maxThreat, threat);
      }
    return maxThreat;
  }

  std::string StarryWisp::toString() const { return "Starry Wisp at " + _target._name; }

  std::string StarryWisp::shorthandStr() const { return "Starry Wisp"; }

  double StarryWisp::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto rollType = battleMap.isEnemyAdjacent(*_factory._combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    int acDifference = std::max(0, std::min(20, _target.getAC() - _factory._toHit));
    int toHitTotal = _factory._toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
    return meanDmg(toHitTotal, {_factory._dmgDice}, 0, _target.getAC(), _target.isImmuneTo(StarryWispFactory::dmgType),
                   _target.isResistantTo(StarryWispFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
  }

  double StarryWisp::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector>
  StarryWisp::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    StarryWispFactory &factory = dynamic_cast<StarryWispFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).getRoot();
    if(swallower)
      {
        if(swallower == &_target)
          {
            CoordVector coords = {currCoord};
            return coords;
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                       static_cast<int>(StarryWispFactory::range), factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= static_cast<int>(StarryWispFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return {};
  }

  void StarryWispEffect::activate(const Kwargs &kwargs)
  {
    if(_combatants.empty())
      {
        return;
      }
    Combatant *target = _combatants[0];
    // The target is lit up: it loses any current Invisible condition and is barred from benefiting from
    // invisibility for the duration.
    target->removeCondition(Conditions::INVISIBLE);
    if(!target->isAffectedBy(Conditions::CANNOT_TURN_INVISIBLE))
      {
        target->applyCondition(Condition(Conditions::CANNOT_TURN_INVISIBLE, _initiator, this, target));
      }
  }

  void StarryWispEffect::deactivate()
  {
    if(_combatants.empty())
      {
        return;
      }
    _combatants[0]->removeCondition(Conditions::CANNOT_TURN_INVISIBLE, _initiator);
  }
}
