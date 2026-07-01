#include "combatants/kobold_warrior.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildKoboldWarrior(KoboldWarrior *self)
    {
      self->setSize(Size::SMALL);

      // Dagger (Melee): +4, 1d4+2 Piercing, reach 5 ft. (finesse -> uses Dexterity).
      // Dagger (Ranged): +4, 1d4+2 Piercing, range 20/60 ft. (long range = 12 cells). The three-dagger loadout is
      // treated as unlimited ammo.
      auto dagger = self->addMeleeAttack("Dagger", self, 4, std::vector<Die>{{1, 4}}, 2, DamageType::Piercing, 1, true);
      auto thrownDagger = self->addRangedAttack("Dagger", self, 4, std::vector<Die>{{1, 4}}, 2, DamageType::Piercing, 12);
      self->addReactionAttack("Dagger", self, 4, std::vector<Die>{{1, 4}}, 2, DamageType::Piercing, 1);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(thrownDagger.get()));

      // Pack Tactics: Advantage on an attack roll against a creature if an ally that isn't Incapacitated is within
      // 5 ft of it. Sunlight Sensitivity (Disadvantage on ability checks and attack rolls in sunlight) has no
      // lighting model and is omitted.
      self->addPackTactics();

      // Single attack: either the melee or thrown Dagger (no multiattack).
      self->addAttackTransition(dagger.get(), AttackFsm::START, AttackFsm::NOP);
      self->addAttackTransition(thrownDagger.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, -2);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, -1);
      self->setSavingThrow(SavingThrow::INT, -1);
      self->setSavingThrow(SavingThrow::WIS, -2);
      self->setSavingThrow(SavingThrow::CHA, -1);
      self->setAthletics(-2);
      self->setAcrobatics(2);
      self->setPassivePerception(8);
    }
  }

  // HP 7 (3d6 - 3), AC 14, Speed 30 ft., Initiative +2.
  KoboldWarrior::KoboldWarrior(int num)
      : Combatant(CombatantType::MONSTER, Monster::DRAGON, _classLevel, concatName(std::string(_className), num), 7, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildKoboldWarrior(this);
  }

  KoboldWarrior::KoboldWarrior(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::DRAGON, _classLevel, name, 7, 14, 2, 0, 30, 0)
  {
    _instanceId = generateInstanceId();
    buildKoboldWarrior(this);
  }
}
