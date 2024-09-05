#pragma once

#include "actions/attack.hpp"
#include <vector>

namespace enc
{

  class RangedAttackFactory : public AttackFactory
  {
  public:
    RangedAttackFactory(const std::string &name, int toHit, std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType,
                        int attackRange, int critRange = 1, Uses &&ammo = Uses(), OnHit *onHit = nullptr,
                        std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false,
                        Die toHitBonusDie = {})
        : AttackFactory(name, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange,
                        std::move(ammo), onHit, extraDmg, usesDex, twoHanded, toHitBonusDie)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;
  };
}