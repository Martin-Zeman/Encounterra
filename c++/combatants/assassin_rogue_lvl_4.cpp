#include "combatants/assassin_rogue_lvl_4.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureAssassinRogueLvl4(AssassinRogueLvl4 *self)
    {
      auto rapier = self->addMeleeAttack("Rapier", self, 6, std::vector<Die>{{1, 8}}, 4, DamageType::Piercing, 1, /*usesDex=*/true);
      auto shortbow = self->addRangedAttack("Shortbow", self, 6, std::vector<Die>{{1, 6}}, 4, DamageType::Piercing, 64, 20);
      self->addReactionAttack("Rapier", self, 6, std::vector<Die>{{1, 8}}, 4, DamageType::Piercing, 1);

      self->addCunningAction();
      self->addSneakAttack();
      self->addAssassinate();

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(shortbow.get()));

      self->setSavingThrow(SavingThrow::STR, -1);
      self->setSavingThrow(SavingThrow::DEX, 6);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(-1);
      self->setAcrobatics(6);
      self->setStealth(8);
      self->setPassivePerception(11);

      self->addAttackTransition(rapier.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(shortbow.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  AssassinRogueLvl4::AssassinRogueLvl4(int num)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, concatName(std::string(_className), num), 27, 16, 4, 0, 30, 14)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl4(this);
  }

  AssassinRogueLvl4::AssassinRogueLvl4(const std::string &name)
      : Combatant(CombatantType::ROGUE, Rogue::ASSASSIN, _classLevel, name, 27, 16, 4, 0, 30, 14)
  {
    _instanceId = generateInstanceId();
    configureAssassinRogueLvl4(this);
  }
}
