#include "spells/firebolt.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>

namespace enc
{

  FireboltFactory::FireboltFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("FireboltFactory", caster, abilityType), _toHit(toHit), _resource(resource),
        _dmgDice(FireboltFactory::getDmgDice(caster->getLevel()))
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant*> FireboltFactory::getEligibleTargets() const
  {
    return {}; // Placeholder
  }

  std::vector<std::shared_ptr<Actoid>> FireboltFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_unique<Firebolt>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> FireboltFactory::create(void *target)
  {
    return std::make_shared<Firebolt>(*static_cast<Combatant*>(target), *this);
  }

  double FireboltFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = target->getSwallower();
    // Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).get()[0];
    if(swallower)
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(FireboltFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        return meanDmg(toHitTotal, {_dmgDice}, 0, target->getAC(), target->isImmuneTo(FireboltFactory::dmgType),
                       target->isResistantTo(FireboltFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
      }

    return 0;
  }

  double FireboltFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers)
  {
        if (target->isImmuneTo(FireboltFactory::dmgType))
    {
        return 0;
    }

    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = targetAC + target->getAC();
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20)));
    double totalCrit = ROLL_TYPE_CRIT_DELTA.at(rollType);

    double modifiedThreat = meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC,
                                    target->isImmuneTo(FireboltFactory::dmgType),
                                    target->isResistantTo(FireboltFactory::dmgType), totalCrit);

    double originalThreat = meanDmg(_toHit, {_dmgDice}, 0, target->getAC(),
                                    target->isImmuneTo(FireboltFactory::dmgType),
                                    target->isResistantTo(FireboltFactory::dmgType), 1);

    return modifiedThreat - originalThreat;
  }

  double FireboltFactory::calculateMaxThreat()
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    double maxThreat = std::numeric_limits<double>::lowest();
    for(const auto &target : eligibleTargets)
      {
        double threat = Firebolt(*target, *this).calculateThreat(Kwargs());
        maxThreat = std::max(maxThreat, threat);
      }
    return maxThreat;
  }

  std::string Firebolt::toString() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_FIREBOLT) ? "Quickened " : "";
    return prefix + "Firebolt at " + _target._name;
  }

  std::string Firebolt::shorthandStr() const
  {
    std::string prefix = (_factory._abilityType == AbilityType::QUICKENED_FIREBOLT) ? "Quickened " : "";
    return prefix + "Firebolt";
  }

  double Firebolt::calculateThreat(const Kwargs &kwargs) { return 0; }
  double Firebolt::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) { return 0; }
  double Firebolt::calculateThreatDelta(/*Add modifiers*/ const Kwargs &kwargs) { return 0; }

  std::optional<std::vector<Coord>>
  Firebolt::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    FireboltFactory &factory = dynamic_cast<FireboltFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).get()[0];
    if(swallower)
      {
        if(swallower == &_target)
          {
            std::vector<Coord> coords = {currCoord};
            return coords;
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                       static_cast<int>(FireboltFactory::range), factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= static_cast<int>(FireboltFactory::range))
      {
        std::vector<Coord> coords = {currCoord};
        return coords;
      }
    return {};
  }
}