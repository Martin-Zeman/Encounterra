#include "combatants/rogue_lvl_1.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureRogueLvl1(RogueLvl1 *self)
    {
      // A finesse rapier wielded with the rogue's Dexterity (+3): +5 to hit, 1d8+3 piercing.
      auto rapier = self->addMeleeAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1, /*usesDex=*/true);
      auto shortbow = self->addRangedAttack("Shortbow", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Piercing, 64, 20);
      self->addReactionAttack("Rapier", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1);

      // Sneak Attack must be attached after the attacks (and reaction) are registered so the on-hit rider is
      // bolted onto every Finesse / ranged weapon.
      self->addSneakAttack();

      // The rogue prefers to threaten a moving enemy with its Shortbow.
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

  RogueLvl1::RogueLvl1(int num)
      : Combatant(CombatantType::ROGUE, Rogue::BEFORE_SUBCLASS, _classLevel, concatName(std::string(_className), num), 9, 14, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureRogueLvl1(this);
  }

  RogueLvl1::RogueLvl1(const std::string &name)
      : Combatant(CombatantType::ROGUE, Rogue::BEFORE_SUBCLASS, _classLevel, name, 9, 14, 3, 0, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureRogueLvl1(this);
  }
}
