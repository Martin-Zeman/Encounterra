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
    //! @todo
    return {};
  }

  std::shared_ptr<Actoid> RangedAttackFactory::create(void *target)
  {
    //! @todo
    return {};
  }

  std::optional<std::vector<Coord>>
  RangedAttack::getEligibleCoords(const blaze::DynamicVector<int> &distances, const blaze::DynamicMatrix<Coord> &shortestPaths)
  {
    return {};
  }
}