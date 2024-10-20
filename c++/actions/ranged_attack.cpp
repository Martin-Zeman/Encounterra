#include "actions/ranged_attack.hpp"
#include "core/interfaces.hpp"

namespace enc
{
  RangedAttackFactory::RangedAttackFactory(const std::string &name, Combatant *combatant, AbilityType abilityType, int toHit,
                                           std::vector<Die> dmgDice, int dmgBonus, DamageType dmgType, int attackRange, int critRange, Uses &&ammo,
                                           std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg, bool usesDex,
                                           bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, combatant, abilityType, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo), std::move(onHit),
                      extraDmg, usesDex, twoHanded, toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_RANGED);
  }

  std::vector<std::shared_ptr<Actoid>> RangedAttackFactory::createAll(void *previousActionInDag)
  {
    auto eligibleTargets = getEligibleTargets();
    std::vector<std::shared_ptr<Actoid>> result;
    result.reserve(eligibleTargets.size());
    for(const auto &target : eligibleTargets)
      {
        result.push_back(std::make_unique<RangedAttack>(*target, *this));
      }
    return result;
  }

  std::shared_ptr<Actoid> RangedAttackFactory::create(void *target)
  {
    return std::make_shared<RangedAttack>(*static_cast<Combatant *>(target), *this);
  }

  std::optional<std::vector<Coord>>
  RangedAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }
}