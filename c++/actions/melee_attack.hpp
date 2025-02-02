#pragma once

#include "actions/attack.hpp"
#include <vector>

namespace enc
{

  class MeleeAttackFactory : public AttackFactory
  {
    friend class MeleeAttack;

  public:
    MeleeAttackFactory(const std::string &name, const std::string &abilityName, Combatant *combatant, AbilityType abilityType, int toHit,
                       std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange = 1, Uses &&ammo = Uses(),
                       std::vector<std::unique_ptr<OnHit>> onHit = {}, std::vector<DmgDieWithType> extraDmg = {}, bool usesDex = false,
                       bool twoHanded = false, Die toHitBonusDie = {});

    std::unique_ptr<AttackFactory> clone() const override { return std::make_unique<MeleeAttackFactory>(*this); }

    std::vector<Actoid *> createAll(void *previousActionInDag = nullptr) override;

    Actoid * create(void *target) override;
  };

  class MeleeAttack : public Attack
  {
  public:
    MeleeAttack(AbilityType abilityType, Combatant &target, AttackFactory &factory) : Attack(abilityType, target, factory) {}

    MeleeAttack(const MeleeAttack &other) : Attack(other._abilityType, other._target, other._factory) {}

    Actoid *clone() const override { return new MeleeAttack(*this); }

    std::optional<CoordVector> getEligibleCoords(const blaze::DynamicVector<int> &distances = blaze::DynamicVector<int>(),
                                                 const blaze::DynamicMatrix<Coord> &shortestPaths = blaze::DynamicMatrix<Coord>()) override;
    bool equals(const Actoid &other) const override;

  protected:
    size_t hash() const override;
  };
}