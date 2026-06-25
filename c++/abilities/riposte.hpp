#pragma once

#include "actions/melee_attack.hpp"
#include "core/resources.hpp"

namespace enc
{
  /**
   * Riposte (Battle Master maneuver, 2024): when an attacker misses the fighter with an attack, the fighter
   * may use its Reaction and spend one Superiority Die to make a melee weapon attack against that attacker,
   * adding the Superiority Die to the damage. Modelled as a MeleeAttackFactory whose damage dice already
   * include the Superiority Die and whose resource is the shared Battle Master Superiority Dice pool (so the
   * reaction is gated/consumed against that pool rather than weapon ammo). It is not offered by the normal
   * planner; it is created on demand by the after-miss reaction hook in the action resolver.
   */
  class RiposteFactory : public MeleeAttackFactory
  {
  public:
    RiposteFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                   int attackRange, Resource *superiorityDice, bool twoHanded = true)
        : MeleeAttackFactory("RiposteFactory", name, combatant, AbilityType::RIPOSTE, toHit, std::move(dmgDice), dmgBonus, dmgType, attackRange, 1,
                             Uses(), {}, {}, false, twoHanded),
          _superiorityDice(superiorityDice)
    {}

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<RiposteFactory>(*this); }

    //! Riposte spends a Superiority Die (the shared Battle Master pool), not weapon ammo.
    std::optional<Resource *> getResource() override { return _superiorityDice; }

  private:
    Resource *_superiorityDice;
  };
}
