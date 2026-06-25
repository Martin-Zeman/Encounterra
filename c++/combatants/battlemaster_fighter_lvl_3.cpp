#include "combatants/battlemaster_fighter_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildBattlemasterFighterLvl3(BattlemasterFighterLvl3 *self)
    {
      // Greatsword (two-handed): +5, 2d6+3 Slashing, reach 5 ft. Carries the Graze mastery.
      auto greatsword = self->addMeleeAttack("Greatsword", self, 5, std::vector<Die>{{2, 6}}, 3, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(greatsword.get())->setTwoHanded(true);
      self->applyWeaponMastery(greatsword, WeaponMastery::GRAZE);

      // Handaxe (thrown, uses Strength): +5, 1d6+3 Slashing, range 30 ft, 2 in hand. Carries the Vex mastery.
      auto handaxe = self->addRangedAttack("Handaxe", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 12, 2);
      self->applyWeaponMastery(handaxe, WeaponMastery::VEX);

      // Opportunity attack with the greatsword (also the basis for the Riposte maneuver).
      auto reaction = self->addReactionAttack("Greatsword", self, 5, std::vector<Die>{{2, 6}}, 3, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(reaction.get())->setTwoHanded(true);

      // Second Wind, Action Surge, Great Weapon Fighting and Battle Master maneuvers (superiority dice).
      // Battle Master must be added after the reaction attack so the Riposte maneuver can reuse it.
      self->addSecondWind();
      self->addTacticalMind();
      self->addActionSurge();
      self->addGreatWeaponFighting();
      self->addBattleMasterManeuvers();

      self->setSavingThrow(SavingThrow::STR, 5);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(5);
      self->setAcrobatics(0);

      // A single attack (Extra Attack is gained at 5th level).
      self->addAttackTransition(greatsword.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(handaxe.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  BattlemasterFighterLvl3::BattlemasterFighterLvl3(int num)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, concatName(std::string(_className), num), 30, 16, 0, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl3(this);
  }

  BattlemasterFighterLvl3::BattlemasterFighterLvl3(const std::string &name)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, name, 30, 16, 0, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl3(this);
  }
}
