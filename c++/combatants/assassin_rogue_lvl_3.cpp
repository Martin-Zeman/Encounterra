#include "combatants/assassin_rogue_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureAssassinRogueLvl3(AssassinRogueLvl3 *self)
    {
      auto rapier = self->addMeleeAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1, /*usesDex=*/true);
      auto shortbow = self->addRangedAttack("Shortbow", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 64, 20);
      self->addReactionAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1);

      // Level 3 Assassin: Cunning Action, Sneak Attack (2d6 at level 3) and Assassinate.
      self->addCunningAction();
      self->addSneakAttack();
      self->addAssassinate();

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(shortbow.get()));

      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 5);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(-1);
      self->setAcrobatics(5);
      self->setStealth(7);
      self->setPassivePerception(11);

      self->addAttackTransition(rapier.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(shortbow.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  AssassinRogueLvl3::AssassinRogueLvl3(int num)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, concatName(std::string(_className), num), 21, 15, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl3(this);
  }

  AssassinRogueLvl3::AssassinRogueLvl3(const std::string &name)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, name, 21, 15, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl3(this);
  }
}
