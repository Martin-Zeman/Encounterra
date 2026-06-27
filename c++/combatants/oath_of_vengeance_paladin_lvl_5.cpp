#include "combatants/oath_of_vengeance_paladin_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildOathOfVengeancePaladinLvl5(OathOfVengeancePaladinLvl5 *self)
    {
      auto battleaxe = self->addMeleeAttack("Battleaxe", self, 7, std::vector<Die>{{1, 8}}, 6, DamageType::Slashing, 1);
      self->applyWeaponMastery(battleaxe, WeaponMastery::TOPPLE);

      auto javelin = self->addRangedAttack("Javelin", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Piercing, 6, 4);
      self->applyWeaponMastery(javelin, WeaponMastery::SLOW);

      self->addReactionAttack("Battleaxe", self, 7, std::vector<Die>{{1, 8}}, 6, DamageType::Slashing, 1);

      self->addSpellSlots();
      self->addCureWounds();
      self->addHoldPerson();
      self->addMistyStep();
      self->addLayOnHands();
      self->addDueling();
      self->addDivineSmite();
      self->addChannelDivinity();
      self->addVowOfEnmity();

      self->setSavingThrow(SavingThrow::STR, 4);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 3);
      self->setSavingThrow(SavingThrow::CHA, 4);
      self->setAthletics(7);
      self->setAcrobatics(-1);

      self->addAttackTransition(battleaxe.get(), AttackFsm::START, 1);
      self->addAttackTransition(battleaxe.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(javelin.get(), AttackFsm::START, 2);
      self->addAttackTransition(javelin.get(), 2, AttackFsm::NOP);
    }
  }

  OathOfVengeancePaladinLvl5::OathOfVengeancePaladinLvl5(int num)
      : Combatant(CombatantType::PALADIN, Paladin::OATH_OF_VENGEANCE, _classLevel, concatName(std::string(_className), num), 44, 18, -1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildOathOfVengeancePaladinLvl5(this);
  }

  OathOfVengeancePaladinLvl5::OathOfVengeancePaladinLvl5(const std::string &name)
      : Combatant(CombatantType::PALADIN, Paladin::OATH_OF_VENGEANCE, _classLevel, name, 44, 18, -1, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildOathOfVengeancePaladinLvl5(this);
  }
}
