#include "combatants/wild_heart_barbarian_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildWildHeartBarbarianLvl5(WildHeartBarbarianLvl5 *self)
    {
      // Two-handed axe (greataxe): +7, 1d12+4 Slashing, reach 5 ft. The greataxe has the Cleave mastery.
      auto axe = self->addMeleeAttack("Two-handed axe", self, 7, std::vector<Die>{{1, 12}}, 4, DamageType::Slashing, 1);
      self->applyWeaponMastery(axe, WeaponMastery::CLEAVE);

      // Javelin (thrown): +7, 1d6+4 Piercing, range 30 ft. The javelin has the Slow mastery.
      auto javelin = self->addRangedAttack("Javelin", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Piercing, 24, 4);
      self->applyWeaponMastery(javelin, WeaponMastery::SLOW);

      // Opportunity attack with the axe.
      self->addReactionAttack("Two-handed axe", self, 7, std::vector<Die>{{1, 12}}, 4, DamageType::Slashing, 1);

      // Reckless Attack: a single axe swing made with Advantage at the cost of being easier to hit.
      auto reckless = self->addRecklessAttack("Two-handed axe recklessly", self, 7, std::vector<Die>{{1, 12}}, 4, DamageType::Slashing, 1);
      self->applyWeaponMastery(reckless, WeaponMastery::CLEAVE);

      // Rage of the Wilds (Bear/Eagle/Wolf), Danger Sense and Unarmored Defense.
      self->addRage();
      self->addDangerSense();
      self->addUnarmoredDefense();

      self->setSavingThrow(SavingThrow::STR, 7);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 7);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(6);
      self->setAcrobatics(1);

      // Extra Attack (5th level): the barbarian makes two axe attacks per turn.
      self->addAttackTransition(axe.get(), AttackFsm::START, 1);
      self->addAttackTransition(axe.get(), 1, AttackFsm::NOP);
    }
  }

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(int num)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, concatName(std::string(_className), num), 61, 15, 1, 0, 40,
                  15)
  {
    _instanceId = generateInstanceId();
    buildWildHeartBarbarianLvl5(this);
  }

  WildHeartBarbarianLvl5::WildHeartBarbarianLvl5(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 61, 15, 1, 0, 40, 15)
  {
    _instanceId = generateInstanceId();
    buildWildHeartBarbarianLvl5(this);
  }
}
