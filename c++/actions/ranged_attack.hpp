#pragma once

#include "actions/attack.hpp"
#include <vector>

namespace enc
{

  class RangedAttackFactory : public AttackFactory
  {
    friend class RangedAttack;

  public:
    RangedAttackFactory(const std::string &name, Combatant *combatant, AbilityType abilityType, int toHit, std::vector<Die> dmgDice, int dmgBonus,
                        DamageType dmgType, int attackRange, int critRange = 1, Uses &&ammo = Uses(), std::vector<std::unique_ptr<OnHit>> onHit = {},
                        std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false, bool twoHanded = false, Die toHitBonusDie = {});

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<RangedAttackFactory>(*this); }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;
  };

  class RangedAttack : public Attack
  {
  public:
    RangedAttack(AbilityType abilityType, Combatant &target, AttackFactory &factory) : Attack(abilityType, target, factory) {}

    std::optional<std::vector<Coord>> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
  };
}