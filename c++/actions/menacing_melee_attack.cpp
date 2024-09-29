#include "actions/menacing_melee_attack.hpp"

namespace enc
{
  MenacingMeleeAttackFactory::MenacingMeleeAttackFactory(const std::string &name, Combatant *combatant, int toHit, std::vector<Die> dmgDice,
                                                         int dmgBonus, DamageType dmgType, int attackRange, int critRange, Uses &&ammo,
                                                         std::vector<std::unique_ptr<OnHit>> onHit, std::vector<DmgDieWithType> extraDmg,
                                                         bool usesDex, bool twoHanded, Die toHitBonusDie)
      : MeleeAttackFactory(name, combatant, toHit, dmgDice, dmgBonus, dmgType, attackRange, critRange, std::move(ammo), std::move(onHit), extraDmg, usesDex,
                           twoHanded, toHitBonusDie)
  {
    initializeMenacingAttack();
  }

  MenacingMeleeAttackFactory::MenacingMeleeAttackFactory(const MeleeAttackFactory &other) : MeleeAttackFactory(other) { initializeMenacingAttack(); }

  void MenacingMeleeAttackFactory::initializeMenacingAttack()
  {
    _name = "Menacing " + _name;
    // _dmgDice.push_back(getSuperiorityCombatant(_combatant->getLevel()));
    // _onHit.push_back(std::make_unique<OnHitSavingThrowEffect>(SavingThrow::WIS, _combatant->getDC(), "Frightened by Menacing Attack"));
    // _actionType = (std::holds_alternative<Action>(_actionType)) ? Action::MENACING_MELEE_ATTACK : BonusAction::BONUS_MENACING_MELEE_ATTACK;
  }

  std::vector<std::shared_ptr<Actoid>> MenacingMeleeAttackFactory::createAll(void *previousActionInDag)
  {
    //! @todo
    return {};
  }

  std::shared_ptr<Actoid> MenacingMeleeAttackFactory::create(void *target)
  {
    //! @todo
    return {};
  }
}