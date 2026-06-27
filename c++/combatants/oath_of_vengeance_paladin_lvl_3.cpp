#include "combatants/oath_of_vengeance_paladin_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildOathOfVengeancePaladinLvl3(OathOfVengeancePaladinLvl3 *self)
    {
      auto battleaxe = self->addMeleeAttack("Battleaxe", self, 5, std::vector<Die>{{1, 8}}, 5, DamageType::Slashing, 1);
      self->applyWeaponMastery(battleaxe, WeaponMastery::TOPPLE);

      auto javelin = self->addRangedAttack("Javelin", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 6, 4);
      self->applyWeaponMastery(javelin, WeaponMastery::SLOW);

      self->addReactionAttack("Battleaxe", self, 5, std::vector<Die>{{1, 8}}, 5, DamageType::Slashing, 1);

      self->addSpellSlots();
      self->addCureWounds();
      self->addLayOnHands();
      self->addDueling();
      self->addDivineSmite();
      self->addChannelDivinity();
      self->addVowOfEnmity();

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 3);
      self->setSavingThrow(SavingThrow::CHA, 4);
      self->setAthletics(5);
      self->setAcrobatics(-1);

      self->addAttackTransition(battleaxe.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(javelin.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  OathOfVengeancePaladinLvl3::OathOfVengeancePaladinLvl3(int num)
      : Combatant(CombatantType::PALADIN, Paladin::OATH_OF_VENGEANCE, _classLevel, concatName(std::string(_className), num), 28, 18, -1, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildOathOfVengeancePaladinLvl3(this);
  }

  OathOfVengeancePaladinLvl3::OathOfVengeancePaladinLvl3(const std::string &name)
      : Combatant(CombatantType::PALADIN, Paladin::OATH_OF_VENGEANCE, _classLevel, name, 28, 18, -1, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildOathOfVengeancePaladinLvl3(this);
  }
}
