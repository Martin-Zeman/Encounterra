#pragma once

#include "actions/melee_attack.hpp"
#include <vector>

namespace enc
{

  class MenacingMeleeAttackFactory : public MeleeAttackFactory
  {
  public:
    MenacingMeleeAttackFactory(const std::string &name, Combatant *combatant, AbilityType abilityType, int toHit, std::vector<Die> dmgDice,
                               int dmgBonus, DamageType dmgType, int attackRange, int critRange = 1, Uses &&ammo = Uses(),
                               std::vector<std::unique_ptr<OnHit>> onHit = {}, std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false,
                               bool twoHanded = false, Die toHitBonusDie = {});

    MenacingMeleeAttackFactory(const MeleeAttackFactory &other);

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<MenacingMeleeAttackFactory>(*this); }

    std::vector<std::shared_ptr<Actoid>> createAll(void *previousActionInDag = nullptr) override;

    std::shared_ptr<Actoid> create(void *target) override;

  private:
    void initializeMenacingAttack();
  };

  class MenacingMeleeAttack : public MeleeAttack//! @todo LimitedDurationEffect
  {
  public:
    MenacingMeleeAttack(AbilityType abilityType, Combatant &target, MenacingMeleeAttackFactory &factory) : MeleeAttack(abilityType, target, factory)
    {}

    std::optional<std::vector<Coord>> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                        const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
  };
}