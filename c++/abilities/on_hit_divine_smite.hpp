#pragma once

#include "abilities/on_hit_effect.hpp"
#include "actions/attack.hpp"
#include "core/interfaces.hpp"
#include "core/resources.hpp"
#include "core/types.hpp"

namespace enc
{
  class Combatant;

  /**
   * Divine Smite (2024 Paladin): modelled as an attack variant. A smiting copy of each melee / unarmed attack
   * consumes the Action and the Bonus Action; this on-hit rider spends the free cast / a spell slot and adds
   * the radiant dice the moment the attack lands.
   */
  class OnHitDivineSmite : public OnHit
  {
  public:
    static Die getDmgDice(int spellSlotLevel);
    static Die getDmgDiceUndeadOrFiend(int spellSlotLevel);
    static bool isUndeadOrFiend(Combatant *target);
    static bool canSmite(Combatant *attacker);
    static int chooseSmiteLevel(Combatant *attacker, Combatant *target, double multiplier = 1.0, double dmgSoFar = 0.0);

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target) override;

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitDivineSmite>(*this); }
  };
}
