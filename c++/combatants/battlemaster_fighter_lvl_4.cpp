#include "combatants/battlemaster_fighter_lvl_4.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildBattlemasterFighterLvl4(BattlemasterFighterLvl4 *self)
    {
      // Greatsword (two-handed): +6, 2d6+4 Slashing, reach 5 ft. Carries the Graze mastery.
      auto greatsword = self->addMeleeAttack("Greatsword", self, 6, std::vector<Die>{{2, 6}}, 4, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(greatsword.get())->setTwoHanded(true);
      self->applyWeaponMastery(greatsword, WeaponMastery::GRAZE);

      // Handaxe (thrown, uses Strength): +6, 1d6+4 Slashing, range 30 ft, 2 in hand. Carries the Vex mastery.
      auto handaxe = self->addRangedAttack("Handaxe", self, 6, std::vector<Die>{{1, 6}}, 4, DamageType::Slashing, 12, 2);
      self->applyWeaponMastery(handaxe, WeaponMastery::VEX);

      // Opportunity attack with the greatsword (also the basis for the Riposte maneuver).
      auto reaction = self->addReactionAttack("Greatsword", self, 6, std::vector<Die>{{2, 6}}, 4, DamageType::Slashing, 1);
      static_cast<AttackFactory *>(reaction.get())->setTwoHanded(true);

      // Second Wind, Action Surge, Great Weapon Fighting and Battle Master maneuvers (superiority dice).
      // Battle Master must be added after the reaction attack so the Riposte maneuver can reuse it.
      self->addSecondWind();
      self->addTacticalMind();
      self->addActionSurge();
      self->addGreatWeaponFighting();
      self->addBattleMasterManeuvers();

      self->setSavingThrow(SavingThrow::STR, 6);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(6);
      self->setAcrobatics(0);

      // A single attack (Extra Attack is gained at 5th level).
      self->addAttackTransition(greatsword.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(handaxe.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  BattlemasterFighterLvl4::BattlemasterFighterLvl4(int num)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, concatName(std::string(_className), num), 38, 16, 0, 0, 30, 14)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl4(this);
  }

  BattlemasterFighterLvl4::BattlemasterFighterLvl4(const std::string &name)
      : Combatant(CombatantType::FIGHTER, Fighter::BATTLE_MASTER, _classLevel, name, 38, 16, 0, 0, 30, 14)
  {
    _instanceId = generateInstanceId();
    buildBattlemasterFighterLvl4(this);
  }
}
