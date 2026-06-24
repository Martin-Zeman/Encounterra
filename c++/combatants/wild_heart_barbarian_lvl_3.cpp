#include "combatants/wild_heart_barbarian_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildWildHeartBarbarianLvl3(WildHeartBarbarianLvl3 *self)
    {
      // Two-handed axe (greataxe): +5, 1d12+3 Slashing, reach 5 ft. The greataxe has the Cleave mastery.
      auto axe = self->addMeleeAttack("Two-handed axe", self, 5, std::vector<Die>{{1, 12}}, 3, DamageType::Slashing, 1);
      self->applyWeaponMastery(axe, WeaponMastery::CLEAVE);

      // Javelin (thrown): +5, 1d6+3 Piercing, range 30 ft. The javelin has the Slow mastery.
      auto javelin = self->addRangedAttack("Javelin", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 24, 4);
      self->applyWeaponMastery(javelin, WeaponMastery::SLOW);

      // Opportunity attack with the axe.
      self->addReactionAttack("Two-handed axe", self, 5, std::vector<Die>{{1, 12}}, 3, DamageType::Slashing, 1);

      // Reckless Attack: a single axe swing made with Advantage at the cost of being easier to hit.
      auto reckless = self->addRecklessAttack("Two-handed axe recklessly", self, 5, std::vector<Die>{{1, 12}}, 3, DamageType::Slashing, 1);
      self->applyWeaponMastery(reckless, WeaponMastery::CLEAVE);

      // Rage of the Wilds (Bear/Eagle/Wolf), Danger Sense and Unarmored Defense.
      self->addRage();
      self->addDangerSense();
      self->addUnarmoredDefense();

      self->setSavingThrow(SavingThrow::STR, 5);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 5);
      self->setSavingThrow(SavingThrow::INT, 1);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(5);
      self->setAcrobatics(1);

      // Single attack at 3rd level (Extra Attack is gained at 5th level).
      self->addAttackTransition(axe.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(int num)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, concatName(std::string(_className), num), 35, 14, 1, 0, 30,
                  13)
  {
    _instanceId = generateInstanceId();
    buildWildHeartBarbarianLvl3(this);
  }

  WildHeartBarbarianLvl3::WildHeartBarbarianLvl3(const std::string &name)
      : Combatant(CombatantType::BARBARIAN, Barbarian::PATH_OF_WILD_HEART, _classLevel, name, 35, 14, 1, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildWildHeartBarbarianLvl3(this);
  }
}