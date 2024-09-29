#include "spells/firebolt.hpp"
#include "core/combatant.hpp"
#include <memory>
#include <limits>

namespace enc
{

  FireboltFactory::FireboltFactory(int toHit, AbilityType abilityType, Combatant *caster, Resource *resource)
      : DirectThreatFactory("FireboltFactory", caster), _toHit(toHit), _abilityType(abilityType), _resource(resource),
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

  double FireboltFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) { return 0; }
  double FireboltFactory::calculateThreatToTargetDelta(Combatant *target /*Add modifiers*/)
  {
    return 0;
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
}