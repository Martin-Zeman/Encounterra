#pragma once

#include <memory>

#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"

namespace enc
{
  class Combatant;
  class Actoid;

  //! Unified on-hit rider implementing the 2024 weapon-mastery properties that trigger on a hit:
  //! Cleave, Push, Sap, Slow, Topple and Vex. Graze and Nick are handled elsewhere (Graze is an on-miss
  //! effect; Nick changes the action economy of the Light extra attack), so for those this rider is a no-op.
  //! Mirrors the side-effect style of OnHitGrapple / OnHitProne and contributes no direct threat of its own.
  class OnHitMastery : public OnHit
  {
  public:
    explicit OnHitMastery(WeaponMastery mastery) : _mastery(mastery) {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override { return 0.0; }

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitMastery>(_mastery); }

  private:
    WeaponMastery _mastery;
  };
}
