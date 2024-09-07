#pragma once

#include "actions/attack.hpp"
#include <vector>

namespace enc
{

  class MeleeAttackFactory : public AttackFactory
  {
  public:
    MeleeAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                       int attackRange, int critRange = 1, Uses &&ammo = Uses(), std::vector<std::unique_ptr<OnHit>> onHit = {},
                       std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false, Die toHitBonusDie = {});

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<MeleeAttackFactory>(*this); }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;
  };
}