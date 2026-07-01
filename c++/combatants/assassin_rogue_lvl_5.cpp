#include "combatants/assassin_rogue_lvl_5.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureAssassinRogueLvl5(AssassinRogueLvl5 *self)
    {
      auto rapier = self->addMeleeAttack("Rapier", self, 7, std::vector<Die>{{1, 8}}, 4, DamageType::Piercing, 1, /*usesDex=*/true);
      auto shortbow = self->addRangedAttack("Shortbow", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Piercing, 64, 20);
      self->addReactionAttack("Rapier", self, 7, std::vector<Die>{{1, 8}}, 4, DamageType::Piercing, 1);

      // Level 5 grants Uncanny Dodge and bumps Sneak Attack to 3d6.
      self->addUncannyDodge();
      self->addCunningAction();
      self->addSneakAttack();
      self->addAssassinate();

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(shortbow.get()));

      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 7);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 5);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(-1);
      self->setAcrobatics(7);
      self->setStealth(10);
      self->setPassivePerception(11);

      self->addAttackTransition(rapier.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(shortbow.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  AssassinRogueLvl5::AssassinRogueLvl5(int num)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, concatName(std::string(_className), num), 33, 16, 4, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl5(this);
  }

  AssassinRogueLvl5::AssassinRogueLvl5(const std::string &name)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, name, 33, 16, 4, 0, 30, 15)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl5(this);
  }
}
