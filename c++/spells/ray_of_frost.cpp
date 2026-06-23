#include "spells/ray_of_frost.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>
#include <algorithm>

namespace enc
{

  RayOfFrostFactory::RayOfFrostFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("RayOfFrostFactory", "Ray of Frost", caster, abilityType), _toHit(toHit), _resource(resource),
        _dmgDice(RayOfFrostFactory::getDmgDice(caster->getLevel()))
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant *> RayOfFrostFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(RayOfFrostFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> RayOfFrostFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<RayOfFrost>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> RayOfFrostFactory::create(void *target)
  {
    return std::make_shared<RayOfFrost>(*static_cast<Combatant *>(target), *this);
  }

  double RayOfFrostFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower())
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(RayOfFrostFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        return meanDmg(toHitTotal, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(RayOfFrostFactory::dmgType),
                       target->isResistantTo(RayOfFrostFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
      }

    return 0;
  }

  double RayOfFrostFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    if(target->isImmuneTo(RayOfFrostFactory::dmgType))
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

    double modifiedThreat = meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC, target->isImmuneTo(RayOfFrostFactory::dmgType),
                                    target->isResistantTo(RayOfFrostFactory::dmgType), totalCrit);

    double originalThreat = meanDmg(_toHit, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(RayOfFrostFactory::dmgType),
                                    target->isResistantTo(RayOfFrostFactory::dmgType), 1);

    return modifiedThreat - originalThreat;
  }

  double RayOfFrostFactory::calculateMaxThreat() const
  {
    auto eligibleTargets = getEligibleTargets();
    double maxThreat = std::numeric_limits<double>::lowest();
    for(const auto &target : eligibleTargets)
      {
        double threat = RayOfFrost(*target, *this).calculateThreat(Kwargs());
        maxThreat = std::max(maxThreat, threat);
      }
    return eligibleTargets.empty() ? 0 : maxThreat;
  }

  std::string RayOfFrost::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_RAY_OF_FROST) ? "Quickened " : "";
    return prefix + "Ray of Frost at " + _target._name;
  }

  std::string RayOfFrost::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_RAY_OF_FROST) ? "Quickened " : "";
    return prefix + "Ray of Frost";
  }

  double RayOfFrost::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto rollType = battleMap.isEnemyAdjacent(*_factory._combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    int acDifference = std::max(0, std::min(20, _target.getAC() - _factory._toHit));
    int toHitTotal = _factory._toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
    return meanDmg(toHitTotal, {_factory._dmgDice}, 0, _target.getAC(), _target.isImmuneTo(RayOfFrostFactory::dmgType),
                   _target.isResistantTo(RayOfFrostFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
  }

  double RayOfFrost::calculateThreatDelta(const ThreatModifiers &modifiers) const
  {
    return _factory.calculateThreatToTargetDelta(&_target, modifiers);
  }

  std::optional<CoordVector>
  RayOfFrost::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    RayOfFrostFactory &factory = dynamic_cast<RayOfFrostFactory &>(getFactory());
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
                                                       static_cast<int>(RayOfFrostFactory::range), factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= static_cast<int>(RayOfFrostFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return {};
  }

  void RayOfFrostEffect::activate(const Kwargs &kwargs)
  {
    if(_applied || _combatants.empty())
      {
        return;
      }
    Combatant *target = _combatants[0];
    int newSpeed = std::max(0, target->getSpeed() - SPEED_REDUCTION);
    target->setSpeed(newSpeed);
    if(target->getMovement() > newSpeed)
      {
        target->setMovement(newSpeed);
      }
    _applied = true;
  }

  void RayOfFrostEffect::deactivate()
  {
    if(!_applied || _combatants.empty())
      {
        return;
      }
    Combatant *target = _combatants[0];
    target->setSpeed(target->getSpeed() + SPEED_REDUCTION);
    _applied = false;
  }
}
