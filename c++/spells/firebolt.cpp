#include "spells/firebolt.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>

namespace enc
{

  FireboltFactory::FireboltFactory(int toHit, AbilityType abilityType, const std::shared_ptr<Combatant> &caster, Resource *resource)
      : DirectThreatFactory("FireboltFactory", "Firebolt", caster, abilityType), _toHit(toHit), _resource(resource),
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

  double FireboltFactory::calculateThreatToTarget(const Combatant &target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    // Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).getRoot();
    if(target.getSwallowerPtr())
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant.lock(), target) <= static_cast<int>(FireboltFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant.lock()) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target.getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        return meanDmg(toHitTotal, {_dmgDice}, 0, target.getAC(), target.isImmuneTo(FireboltFactory::dmgType),
                       target.isResistantTo(FireboltFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
      }

    return 0;
  }

  double FireboltFactory::calculateThreatToTargetDelta(const Combatant &target, const ThreatModifiers &modifiers) const
  {
    if(target.isImmuneTo(FireboltFactory::dmgType))
      {
        return 0;
      }

    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = targetAC + target.getAC();
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    int needToRollAtLeast = std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20));
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(needToRollAtLeast);
    double totalCrit = ROLL_TYPE_CRIT_DELTA.at(rollType);

    double modifiedThreat = meanDmg(toHitTotal, {_dmgDice}, 0, totalTargetAC, target.isImmuneTo(FireboltFactory::dmgType),
                                    target.isResistantTo(FireboltFactory::dmgType), totalCrit);

    double originalThreat = meanDmg(_toHit, {_dmgDice}, 0, target.getAC(), target.isImmuneTo(FireboltFactory::dmgType),
                                    target.isResistantTo(FireboltFactory::dmgType), 1);

    return modifiedThreat - originalThreat;
  }

  double FireboltFactory::calculateMaxThreat() const
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

  double Firebolt::calculateThreat(const Kwargs &kwargs)
  {
    BattleMap &battleMap = BattleMap::getInstance();
    auto rollType = battleMap.isEnemyAdjacent(*(_factory._combatant.lock())) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
    int acDifference = std::max(0, std::min(20, _target.getAC() - _factory._toHit));
    int toHitTotal = _factory._toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
    return meanDmg(toHitTotal, {_factory._dmgDice}, 0, _target.getAC(), _target.isImmuneTo(FireboltFactory::dmgType),
                   _target.isResistantTo(FireboltFactory::dmgType), ROLL_TYPE_CRIT_DELTA.at(rollType));
  }

  // Default
  // double Firebolt::calculateThreatForAttack(Combatant *attacker, Actoid *attack, const Kwargs &kwargs) { return 0; }

  double Firebolt::calculateThreatDelta(const ThreatModifiers &modifiers) const { 
    return _factory.calculateThreatToTargetDelta(_target, modifiers);
   }

  std::optional<CoordVector>
  Firebolt::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    FireboltFactory &factory = dynamic_cast<FireboltFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    auto combatant = factory._combatant.lock();
    Coord currCoord = battleMap.getCombatantCoordinates(*combatant).getRoot();
    if(auto swallower = combatant->getSwallowerPtr())
      {
        if(*swallower == _target)
          {
            CoordVector coords = {currCoord};
            return coords;
          }
        return {};
      }

    if(!combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, combatant->getSize(),
                                                       static_cast<int>(FireboltFactory::range), combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*combatant, _target) <= static_cast<int>(FireboltFactory::range))
      {
        CoordVector coords = {currCoord};
        return coords;
      }
    return {};
  }

  size_t Firebolt::hash() const
  {
    size_t h = std::hash<int>{}(static_cast<int>(getAbilityType()));
    h ^= std::hash<int>{}(static_cast<int>(getFlags())) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(_target._instanceId) + 0x9e3779b9 + (h << 6) + (h >> 2);
    h ^= std::hash<int>{}(static_cast<int>(_rollType)) + 0x9e3779b9 + (h << 6) + (h >> 2);
    return h;
  }

  bool Firebolt::equals(const Actoid &other) const
  {
    if(auto *firebolt = dynamic_cast<const Firebolt *>(&other))
      {
        return getAbilityType() == other.getAbilityType() && getFlags() == other.getFlags() && _target._instanceId == firebolt->_target._instanceId
               && _rollType == firebolt->_rollType;
      }
    return false;
  }
}