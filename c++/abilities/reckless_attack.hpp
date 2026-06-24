#pragma once

#include "actions/melee_attack.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"
#include <vector>

namespace enc
{

  /**
   * Reckless Attack (Barbarian, level 2+). As an attack on its turn the barbarian can attack recklessly,
   * gaining Advantage on Strength-based melee attack rolls until the start of its next turn — but attack
   * rolls against it also have Advantage during that time. Modelled (like Python's reckless_attack.py) as a
   * single two-handed melee Action whose threat is the Advantage damage minus a heuristic for the extra
   * damage the barbarian exposes itself to. The lingering "attacks against me have Advantage" downside is the
   * RecklessAttack effect, which resolveAttack consults.
   */
  class RecklessAttackFactory : public MeleeAttackFactory
  {
    friend class RecklessAttack;

  public:
    RecklessAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                          int attackRange);

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<RecklessAttackFactory>(*this); }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;
    std::shared_ptr<Actoid> create(void *target) override;

    double calculateThreatToTarget(Combatant *target, const Kwargs &kwargs) const override;
  };

  class RecklessAttack : public MeleeAttack, public CombatantEffect, public LimitedDurationEffect
  {
  public:
    RecklessAttack(Combatant &target, RecklessAttackFactory &factory);

    EffectType getEffectType() const override { return EffectType::RECKLESS_ATTACK; }
    // The benefit (Advantage on the barbarian's own attacks) and the downside (Advantage on attacks against
    // it) are both applied at resolution time by resolveAttack, which checks for this effect; nothing extra
    // needs to be toggled on activation.
    void activate(const Kwargs &kwargs = {}) override {}
    void deactivate() override {}
    bool deactivateForCombatant(Combatant *combatant) override { return true; }
  };
}
