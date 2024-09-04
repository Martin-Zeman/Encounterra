#pragma once

#include "actions/attack.hpp"
#include <vector>

namespace enc
{

  class RangedAttackFactory : public AttackFactory
  {
  public:
    RangedAttackFactory(const std::string &name, int toHit, std::vector<std::pair<int, int>> dmgDice, int dmgBonus, DamageType dmgType,
                       int attackRange)
        : AttackFactory(name, toHit, dmgDice, dmgBonus, dmgType, attackRange)
    {}

    std::vector<std::shared_ptr<Actoid>> createAll(void *previous_action_in_dag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;
  };
}
