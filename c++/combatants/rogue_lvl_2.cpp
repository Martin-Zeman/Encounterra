#include "combatants/rogue_lvl_2.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureRogueLvl2(RogueLvl2 *self)
    {
      auto rapier = self->addMeleeAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1, /*usesDex=*/true);
      auto shortbow = self->addRangedAttack("Shortbow", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 64, 20);
      self->addReactionAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1);

      // Level 2: Cunning Action (bonus-action Dash / Disengage / Hide) plus Sneak Attack.
      self->addCunningAction();
      self->addSneakAttack();

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

  RogueLvl2::RogueLvl2(int num)
      : Combatant(CombatantType::ROGUE, Rogue::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 15, 14, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureRogueLvl2(this);
  }

  RogueLvl2::RogueLvl2(const std::string &name)
      : Combatant(CombatantType::ROGUE, Rogue::BEFORE_SUBCLASS, _classLevel, name, 15, 14, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureRogueLvl2(this);
  }
}
