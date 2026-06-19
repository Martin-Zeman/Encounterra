#pragma once

#include <memory>
#include <string>
#include <utility>
#include <vector>
#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"

namespace enc
{
  class Combatant;
  class Actoid;

  /**
   * On-hit rider that applies the 2024 Grappled condition.
   *
   * Mirrors the Python simulator/abilities/on_hit_auto_restrained.py, adapted to the 2024 rules:
   * the 2024 Grab applies only the Grappled condition (it does NOT also Restrain). On a hit, if the
   * target is not already grappled, it gains the Grappled condition (escape DC = _dc, escaped on the
   * grappled creature's action with a Strength (Athletics) or Dexterity (Acrobatics) check) and the
   * attacker gains the Grappling condition pointing at the target.
   *
   * Contributes no threat (grapple is a control effect, not damage).
   */
  class OnHitGrapple : public OnHit
  {
  public:
    explicit OnHitGrapple(int dc, SkillCheck escapeSkill = SkillCheck::ATHLETICS)
        : _dc(dc), _escapeSkill(escapeSkill) {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override { return 0.0; }

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitGrapple>(_dc, _escapeSkill); }

  private:
    int _dc;
    SkillCheck _escapeSkill;
  };
}
