#include "wizard_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureWizardLvl1(WizardLvl1 *self)
    {
      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 5);
      self->setSavingThrow(SavingThrow::WIS, 4);
      self->setSavingThrow(SavingThrow::CHA, 0);

      auto dagger = self->addMeleeAttack("Dagger", self, 3, std::vector<Die>{{1, 4}}, 1, DamageType::Piercing, 1);
      auto quarterstaff = self->addMeleeAttack("Quarterstaff", self, 1, std::vector<Die>{{1, 6}}, -1, DamageType::Bludgeoning, 1);

      self->addSpellSlots();
      self->addMageArmor(14);
      self->addMagicMissile();
      self->addSleep();
      self->addRayOfFrost();

      self->addAttackTransition(dagger.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(quarterstaff.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  WizardLvl1::WizardLvl1(int num)
      : Combatant(CombatantType::WIZARD, Wizard::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 7, 11, 1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWizardLvl1(this);
  }

  WizardLvl1::WizardLvl1(const std::string &name)
      : Combatant(CombatantType::WIZARD, Wizard::BEFORE_SUBCLASS, _classLevel, name, 7, 11, 1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureWizardLvl1(this);
  }
}
