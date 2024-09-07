#pragma once

#include "actions/melee_attack.hpp"
#include <vector>

namespace enc
{

  class MenacingMeleeAttackFactory : public MeleeAttackFactory
  {
  public:
    MenacingMeleeAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                               int attackRange, int critRange = 1, Uses &&ammo = Uses(), std::vector<std::unique_ptr<OnHit>> onHit = {},
                               std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false, Die toHitBonusDie = {});

    MenacingMeleeAttackFactory(const MeleeAttackFactory &other);

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<MenacingMeleeAttackFactory>(*this); }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

  private:
    void initializeMenacingAttack();
  };
}