#include "combatants/paladin_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildPaladinLvl1(PaladinLvl1 *self)
    {
      auto battleaxe = self->addMeleeAttack("Battleaxe", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);
      self->applyWeaponMastery(battleaxe, WeaponMastery::TOPPLE);

      auto javelin = self->addRangedAttack("Javelin", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 6, 4);
      self->applyWeaponMastery(javelin, WeaponMastery::SLOW);

      self->addReactionAttack("Battleaxe", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);

      self->addSpellSlots();
      self->addCureWounds();
      self->addLayOnHands();

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

  PaladinLvl1::PaladinLvl1(int num)
      : Combatant(CombatantType::PALADIN, Paladin::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 12, 18, -1, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildPaladinLvl1(this);
  }

  PaladinLvl1::PaladinLvl1(const std::string &name)
      : Combatant(CombatantType::PALADIN, Paladin::BEFORE_SUBCLASS, _classLevel, name, 12, 18, -1, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildPaladinLvl1(this);
  }
}
