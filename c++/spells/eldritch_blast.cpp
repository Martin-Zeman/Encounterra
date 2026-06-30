#include "spells/eldritch_blast.hpp"
#include "core/combatant.hpp"
#include "core/battle_map.hpp"
#include <memory>
#include <limits>

namespace enc
{

  EldritchBlastFactory::EldritchBlastFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("EldritchBlastFactory", "Eldritch Blast", caster, abilityType), _toHit(toHit), _resource(resource),
        _numBeams(EldritchBlastFactory::getNumBeams(caster->getLevel()))
  {
    setFlag(FactoryFlags::IS_ATTACK_LIKE);
  }

  std::vector<Combatant *> EldritchBlastFactory::getEligibleTargets() const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = _combatant->getSwallower();
    if(swallower)
      {
        return {swallower};
      }
    return battleMap.getNonSwallowedEnemiesWithinRadius(_combatant, static_cast<int>(EldritchBlastFactory::range));
  }

  std::vector<std::shared_ptr<Actoid>> EldritchBlastFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_shared<EldritchBlast>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> EldritchBlastFactory::create(void *target)
  {
    return std::make_shared<EldritchBlast>(*static_cast<Combatant *>(target), *this);
  }

  double EldritchBlastFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    BattleMap &battleMap = BattleMap::getInstance();
    if(target->getSwallower())
      {
        return 0;
      }
    if(battleMap.getCartesianDistanceCombatants(*_combatant, *target) <= static_cast<int>(EldritchBlastFactory::range))
      {
        auto rollType = battleMap.isEnemyAdjacent(*_combatant) ? RollType::DISADVANTAGE : RollType::STRAIGHT;
        int acDifference = std::max(0, std::min(20, target->getAC() - _toHit));
        int toHitTotal = _toHit + ROLL_TYPE_DELTA.at(rollType).at(acDifference);
        // Every beam is a separate attack roll; the threat-maximising play aims all of them at this target.
        double singleBeam = meanDmg(toHitTotal, {EldritchBlastFactory::beamDmgDice}, _dmgBonus, target->getAC(),
                                    target->isImmuneTo(EldritchBlastFactory::dmgType), target->isResistantTo(EldritchBlastFactory::dmgType),
                                    ROLL_TYPE_CRIT_DELTA.at(rollType));
        return singleBeam * _numBeams;
      }

    return 0;
  }

  double EldritchBlastFactory::calculateThreatToTargetDelta(Combatant *target, const ThreatModifiers &modifiers) const
  {
    if(target->isImmuneTo(EldritchBlastFactory::dmgType))
      {
        return 0;
      }

    int modToHitFlat = modifiers.getOrDefault(ThreatModifierType::TO_HIT_FLAT, 0);
    Die modToHitDie = modifiers.getOrDefault(ThreatModifierType::TO_HIT_DIE, Die{0, 0});
    std::vector<Die> modDmgDie = modifiers.getOrDefault(ThreatModifierType::DMG_BONUS_DIE, std::vector<Die>{{0, 0}});
    int modDmgFlat = modifiers.getOrDefault(ThreatModifierType::DMG_BONUS_FLAT, 0);
    RollType rollType = modifiers.getOrDefault(ThreatModifierType::ROLL_TYPE, RollType::STRAIGHT);
    int targetAC = modifiers.getOrDefault(ThreatModifierType::TARGET_AC, 0);

    int totalTargetAC = targetAC + target->getAC();
    double toHitTotal = _toHit + modToHitFlat + avgRoll(modToHitDie);
    int needToRollAtLeast = std::max(0, std::min(totalTargetAC - static_cast<int>(toHitTotal), 20));
    toHitTotal += ROLL_TYPE_DELTA.at(rollType).at(needToRollAtLeast);
    double totalCrit = ROLL_TYPE_CRIT_DELTA.at(rollType);

    // The damage-die modifier (e.g. Hex's +1d6 Necrotic) lands on every beam, so it is rolled per beam.
    std::vector<Die> modifiedDice = {EldritchBlastFactory::beamDmgDice};
    modifiedDice.insert(modifiedDice.end(), modDmgDie.begin(), modDmgDie.end());

    double modified = meanDmg(toHitTotal, modifiedDice, modDmgFlat + _dmgBonus, totalTargetAC, target->isImmuneTo(EldritchBlastFactory::dmgType),
                              target->isResistantTo(EldritchBlastFactory::dmgType), totalCrit);

    double originalThreat = meanDmg(_toHit, {EldritchBlastFactory::beamDmgDice}, _dmgBonus, target->getAC(),
                                    target->isImmuneTo(EldritchBlastFactory::dmgType), target->isResistantTo(EldritchBlastFactory::dmgType), 1);

    return (modified - originalThreat) * _numBeams;
  }

  double EldritchBlastFactory::calculateMaxThreat() const
  {
    auto eligibleTargets = getEligibleTargets();
    double maxThreat = std::numeric_limits<double>::lowest();
    for(const auto &target : eligibleTargets)
      {
        double threat = EldritchBlast(*target, *this).calculateThreat(Kwargs());
        maxThreat = std::max(maxThreat, threat);
      }
    return maxThreat;
  }

  std::string EldritchBlast::toString() const { return "Eldritch Blast at " + _target._name; }

  std::string EldritchBlast::shorthandStr() const { return "Eldritch Blast"; }

  double EldritchBlast::calculateThreat(const Kwargs &kwargs) { return _factory.calculateThreatToTarget(&_target, kwargs); }

  double EldritchBlast::calculateThreatDelta(const ThreatModifiers &modifiers) const { return _factory.calculateThreatToTargetDelta(&_target, modifiers); }

  std::optional<CoordVector>
  EldritchBlast::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    EldritchBlastFactory &factory = dynamic_cast<EldritchBlastFactory &>(getFactory());
    BattleMap &battleMap = BattleMap::getInstance();
    Combatant *swallower = factory._combatant->getSwallower();
    Coord currCoord = battleMap.getCombatantCoordinates(*factory._combatant).getRoot();
    if(swallower)
      {
        if(swallower == &_target)
          {
            return CoordVector{currCoord};
          }
        return {};
      }

    if(!factory._combatant->isAffectedByAny({Conditions::GRAPPLED, Conditions::GRAPPLING, Conditions::RESTRAINED}))
      {
        return battleMap.getFreeCoordsInCartesianRange(battleMap.getCombatantCoordinates(_target).get(), distances, factory._combatant->getSize(),
                                                       static_cast<int>(EldritchBlastFactory::range), factory._combatant->_instanceId);
      }
    else if(battleMap.getCartesianDistanceCombatants(*factory._combatant, _target) <= static_cast<int>(EldritchBlastFactory::range))
      {
        return CoordVector{currCoord};
      }
    return {};
  }
}
