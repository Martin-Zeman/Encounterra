#pragma once

#include "core/misc.hpp"
#include "effects/combatant_effect.hpp"
#include "effects/limited_duration_effect.hpp"

namespace enc
{
  class Combatant;

  //! Slow mastery rider: on a hit the target's Speed drops by 10 ft (2 cells) until the start of the
  //! wielder's next turn. Modeled as a one-turn limited-duration effect owned by the wielder, mirroring the
  //! Ray of Frost speed-reduction rider.
  class SlowedEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    SlowedEffect(Combatant *wielder, Combatant *target)
        : Effect(wielder), CombatantEffect(wielder, {target}), LimitedDurationEffect(wielder, 1)
    {}

    EffectType getEffectType() const override { return EffectType::SLOWED; }
    void activate(const Kwargs &kwargs = {}) override;
    void deactivate() override;
    bool deactivateForCombatant(Combatant *combatant) override { return true; }

  private:
    static constexpr int SPEED_REDUCTION = 2; // 10 ft expressed in 5-ft cells
    bool _applied = false;
  };

  //! Sap mastery rider: on a hit the target has Disadvantage on its next attack roll before the wielder's
  //! next turn. A pure marker (consumed in resolveAttack). Owned by the sapped creature so it expires on the
  //! sapped creature's turn if it never attacks.
  class SappedEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    explicit SappedEffect(Combatant *target)
        : Effect(target), CombatantEffect(target, {target}), LimitedDurationEffect(target, 1)
    {}

    EffectType getEffectType() const override { return EffectType::SAPPED; }
    void activate(const Kwargs &kwargs = {}) override {}
    void deactivate() override {}
    bool deactivateForCombatant(Combatant *combatant) override { return true; }
  };

  //! Vex mastery rider: on a hit the wielder has Advantage on its next attack roll against that target. A
  //! pure marker (consumed in resolveAttack). Owned by the wielder, pointing at the vexed target.
  class VexedEffect : public CombatantEffect, public LimitedDurationEffect
  {
  public:
    VexedEffect(Combatant *wielder, Combatant *target)
        : Effect(wielder, target), CombatantEffect(wielder, {}), LimitedDurationEffect(wielder, 1)
    {}

    EffectType getEffectType() const override { return EffectType::VEXED; }
    void activate(const Kwargs &kwargs = {}) override {}
    void deactivate() override {}
    bool deactivateForCombatant(Combatant *combatant) override { return true; }
  };
}
