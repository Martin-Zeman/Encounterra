#pragma once

#include "abilities/on_hit_effect.hpp"
#include "core/misc.hpp"
#include "core/types.hpp"
#include <string>
#include <vector>

namespace enc
{
  class Combatant;

  /**
   * Sneak Attack (2024 Rogue). Modelled as an on-hit rider attached to every Finesse or ranged weapon attack
   * the rogue has. Once per turn, when the rogue hits with such an attack and either has Advantage on the roll
   * or an ally of the rogue is adjacent to the target (and the rogue does not have Disadvantage), it deals the
   * extra Sneak Attack dice. Mirrors Python abilities/on_hit_sneak_attack.OnHitSneakAttack.
   */
  class OnHitSneakAttack : public OnHit
  {
  public:
    //! Sneak Attack damage dice by Rogue level: 1d6 at levels 1-2, +1d6 every two levels (ceil(level/2) d6).
    static Die getDmgDice(int level);

    OnHitSneakAttack(std::vector<Die> dmgDice, DamageType dmgType, int critRange, std::string name = "Sneak Attack")
        : _dmgDice(std::move(dmgDice)), _dmgType(dmgType), _critRange(critRange), _name(std::move(name))
    {}

    std::vector<std::pair<int, DamageType>>
    hit(Combatant *attacker, Actoid *attack, Combatant *target, double multiplier, double dmgSoFar) override;

    double calculateThreat(Combatant *attacker, Combatant *target, RollType rollType = RollType::STRAIGHT) override;

    std::unique_ptr<OnHit> clone() const override { return std::make_unique<OnHitSneakAttack>(*this); }

  private:
    std::vector<Die> _dmgDice;
    DamageType _dmgType;
    int _critRange;
    std::string _name;
  };
}
