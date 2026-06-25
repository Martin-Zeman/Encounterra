#include "combatants/fighter_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildFighterLvl1(FighterLvl1 *self)
    {
      // Greatsword (two-handed): +5, 2d6+3 Slashing, reach 5 ft. Carries the Graze mastery.
      auto greatsword = self->addMeleeAttack("Greatsword", self, 5, std::vector<Die>{{2, 6}}, 3, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(greatsword.get())->setTwoHanded(true);
      self->applyWeaponMastery(greatsword, WeaponMastery::GRAZE);

      // Handaxe (thrown, uses Strength): +5, 1d6+3 Slashing, range 30 ft, 2 in hand. Carries the Vex mastery.
      auto handaxe = self->addRangedAttack("Handaxe", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 12, 2);
      self->applyWeaponMastery(handaxe, WeaponMastery::VEX);

      // Opportunity attack with the greatsword.
      auto reaction = self->addReactionAttack("Greatsword", self, 5, std::vector<Die>{{2, 6}}, 3, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(reaction.get())->setTwoHanded(true);

      // Second Wind and the Great Weapon Fighting fighting style.
      self->addSecondWind();
      self->addGreatWeaponFighting();

      self->setSavingThrow(SavingThrow::STR, 5);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(5);
      self->setAcrobatics(0);

      // A single attack at 1st level (Extra Attack is gained at 5th level).
      self->addAttackTransition(greatsword.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(handaxe.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  FighterLvl1::FighterLvl1(int num)
      : Combatant(CombatantType::FIGHTER, Fighter::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 12, 16, 0, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildFighterLvl1(this);
  }

  FighterLvl1::FighterLvl1(const std::string &name)
      : Combatant(CombatantType::FIGHTER, Fighter::BEFORE_SUBCLASS, _classLevel, name, 12, 16, 0, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildFighterLvl1(this);
  }
}
