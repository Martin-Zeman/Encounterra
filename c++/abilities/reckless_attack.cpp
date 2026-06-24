#include "abilities/reckless_attack.hpp"
#include "core/combatant.hpp"
#include "core/threat_utils.hpp"
#include "core/threat_modifiers.hpp"
#include <algorithm>
#include <cmath>

namespace enc
{
  RecklessAttackFactory::RecklessAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus,
                                               DamageType dmgType, int attackRange)
      : MeleeAttackFactory(name, name, combatant, AbilityType::RECKLESS_ATTACK, toHit, std::move(dmgDice), dmgBonus, dmgType, attackRange,
                           /*critRange=*/1, Uses(), /*onHit=*/{}, /*extraDmg=*/{}, /*usesDex=*/false, /*twoHanded=*/true)
  {}

  std::vector<std::shared_ptr<Actoid>> RecklessAttackFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(auto *target : eligibleTargets)
      {
        result.push_back(std::make_shared<RecklessAttack>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> RecklessAttackFactory::create(void *target)
  {
    return std::make_shared<RecklessAttack>(*static_cast<Combatant *>(target), *this);
  }

  double RecklessAttackFactory::calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const
  {
    // Upside: the attack is made with Advantage.
    ThreatModifiers advantage;
    advantage.set(ThreatModifierType::ROLL_TYPE, RollType::ADVANTAGE);
    const double advantageThreat = MeleeAttackFactory::calculateThreatToTarget(target, kwargs) + AttackFactory::calculateThreatToTargetDelta(target, advantage);

    // Downside: until the barbarian's next turn, nearby enemies attack it with Advantage. Estimate the extra
    // damage that exposure would let them deal and discount the reckless attack's value by half of it.
    const double extraIncoming =
        std::abs(calculateThreatInDelta(_combatant, 6, advantage, static_cast<uint32_t>(FactoryFlags::IS_ATTACK_LIKE)).second);

    const double threat = advantageThreat - extraIncoming / 2.0;
    return threat > 0.0 ? threat : 0.0;
  }

  RecklessAttack::RecklessAttack(Combatant &target, RecklessAttackFactory &factory)
      : Effect(factory.getCombatant()), MeleeAttack(AbilityType::RECKLESS_ATTACK, target, factory),
        CombatantEffect(factory.getCombatant(), {factory.getCombatant()}), LimitedDurationEffect(factory.getCombatant(), 1)
  {}
}
