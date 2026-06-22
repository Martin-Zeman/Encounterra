#pragma once

#include <memory>
#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"

namespace enc
{
  class Combatant;
  class Actoid;

  /**
   * On-hit rider that knocks the target Prone unless it succeeds on a saving throw.
   *
   * Mirrors the Python simulator/abilities/on_hit_prone.py. On a hit, the target rolls the given
   * saving throw against _dc; on a failure it gains the Prone condition. Applies no extra damage and
   * (like the grapple rider) contributes no direct threat of its own.
   */
  class OnHitProne : public OnHit
  {
  public:
    OnHitProne(SavingThrow saveType, int dc) : _saveType(saveType), _dc(dc) {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override { return 0.0; }

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitProne>(_saveType, _dc); }

  private:
    SavingThrow _saveType;
    int _dc;
  };
}
