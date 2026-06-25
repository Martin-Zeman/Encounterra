#include "battlemaster_fighter_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildBattlemasterFighterLvl5(BattlemasterFighterLvl5 *self)
    {
      // Greatsword (two-handed): +7, 2d6+4 Slashing, reach 5 ft. Carries the Graze mastery.
      auto greatsword = self->addMeleeAttack("Greatsword", self, 7, std::vector<Die>{{2, 6}}, 4, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(greatsword.get())->setTwoHanded(true);
      self->applyWeaponMastery(greatsword, WeaponMastery::GRAZE);

      // Handaxe (thrown, uses Strength): +7, 1d6+4 Slashing, range 30 ft, 2 in hand. Carries the Vex mastery.
      auto handaxe = self->addRangedAttack("Handaxe", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Slashing, 12, 2);
      self->applyWeaponMastery(handaxe, WeaponMastery::VEX);

      // Opportunity attack with the greatsword (also the basis for the Riposte maneuver).
      auto reaction = self->addReactionAttack("Greatsword", self, 7, std::vector<Die>{{2, 6}}, 4, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(reaction.get())->setTwoHanded(true);

      // Second Wind, Action Surge, Great Weapon Fighting and Battle Master maneuvers (superiority dice).
      // Battle Master must be added after the reaction attack so the Riposte maneuver can reuse it.
      self->addSecondWind();
      self->addTacticalMind();
      self->addActionSurge();
      self->addGreatWeaponFighting();
      self->addBattleMasterManeuvers();

      self->setSavingThrow(SavingThrow::STR, 7);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 5);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(7);
      self->setAcrobatics(0);

      // Extra Attack (5th level): two attacks per turn with the same weapon.
      self->addAttackTransition(greatsword.get(), AttackFsm::START, 1);
      self->addAttackTransition(greatsword.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(handaxe.get(), AttackFsm::START, 2);
      self->addAttackTransition(handaxe.get(), 2, AttackFsm::NOP);
    }
  }

  BattlemasterFighterLvl5::BattlemasterFighterLvl5(int num)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, concatName(std::string(_className), num), 46, 17, 0, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl5(this);
  }

  BattlemasterFighterLvl5::BattlemasterFighterLvl5(const std::string &name)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, name, 46, 17, 0, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl5(this);
  }
}