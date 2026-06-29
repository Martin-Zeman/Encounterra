#pragma once

#include "actions/melee_attack.hpp"

namespace enc
{
  /**
   * Divine Smite (2024 Paladin), modelled as an attack variant. When a Paladin learns Divine Smite, a smite
   * variant of every melee / unarmed attack is registered. The variant consumes both the Action and the
   * Bonus Action and carries an OnHitDivineSmite rider that spends the free cast / a spell slot and adds the
   * radiant dice immediately when the attack lands. With Extra Attack the smite variant occupies one node of
   * the multiattack sequence (delegating to its base attack's FSM transitions); the remaining attacks resolve
   * normally without smite.
   */
  class SmiteMeleeAttackFactory : public MeleeAttackFactory
  {
  public:
    //! Clone an existing melee attack factory into a smite-consuming variant. The base pointer is kept so the
    //! multiattack FSM (keyed on the base attack) and resource bookkeeping can delegate to the original attack.
    SmiteMeleeAttackFactory(const MeleeAttackFactory &base, const ActoidFactory *baseFactory);

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<SmiteMeleeAttackFactory>(*this); }

    const ActoidFactory *getBaseFactory() const { return _baseFactory; }

  private:
    const ActoidFactory *_baseFactory;
  };
}
