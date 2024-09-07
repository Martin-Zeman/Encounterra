#include "actions/ranged_attack.hpp"
#include "core/interfaces.hpp"

namespace enc
{
  RangedAttackFactory::RangedAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice, int dmgBonus,
                                           DamageType dmgType, int attackRange, int critRange, Uses &&ammo, std::vector<std::unique_ptr<OnHit>> onHit,
                                           std::vector<DmgDieWithType> extraDmg, bool usesDex, bool twoHanded, Die toHitBonusDie)
      : AttackFactory(name, combatant, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo), std::move(onHit), extraDmg, usesDex,
                      twoHanded, toHitBonusDie)
  {
    setFlag(FactoryFlags::IS_RANGED);
  }

  std::vector<std::shared_ptr<Actoid>> RangedAttackFactory::createAll(void *previous_action_in_dag)
  {
    //! @todo
    return {};
  }

  std::shared_ptr<Actoid> RangedAttackFactory::create(void *target)
  {
    //! @todo
    return {};
  }
}