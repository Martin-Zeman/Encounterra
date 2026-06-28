#include "combatants/cleric_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureClericLvl1(ClericLvl1 *self)
    {
      auto mace = self->addMeleeAttack("Mace", self, 4, std::vector<Die>{{1, 6}}, 2, DamageType::Bludgeoning, 1);
      self->applyWeaponMastery(mace, WeaponMastery::SAP);
      self->addReactionAttack("Mace", self, 4, std::vector<Die>{{1, 6}}, 2, DamageType::Bludgeoning, 1);

      self->addSpellSlots();
      self->addSacredFlame();
      self->addTollTheDead();
      self->addBless();
      self->addCureWounds();
      self->addGuidingBolt();
      self->addShieldOfFaith();

      self->setSavingThrow(SavingThrow::STR, 2);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 5);
      self->setSavingThrow(SavingThrow::CHA, 3);
      self->setAthletics(2);
      self->setAcrobatics(-1);

      self->addAttackTransition(mace.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  ClericLvl1::ClericLvl1(int num)
      : Combatant(CombatantType::CLERIC, Cleric::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 9, 14, -1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureClericLvl1(this);
  }

  ClericLvl1::ClericLvl1(const std::string &name)
      : Combatant(CombatantType::CLERIC, Cleric::BEFORE_SUBCLASS, _classLevel, name, 9, 14, -1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureClericLvl1(this);
  }
}
