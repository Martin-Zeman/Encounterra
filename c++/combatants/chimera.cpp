#include "combatants/chimera.hpp"
#include "abilities/on_hit_prone.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildChimera(Chimera *self)
    {
      self->setSize(Size::LARGE);

      // Multiattack: one Ram, one Bite and one Claw, in any order.
      // Ram: +7, 1d12+4 Bludgeoning, reach 5 ft. On a hit a Medium or smaller target has the Prone condition
      // (no save, 2024 statblock).
      std::vector<std::unique_ptr<OnHit>> ramRiders;
      ramRiders.push_back(std::make_unique<OnHitProne>(Size::MEDIUM));
      auto ram = self->addMeleeAttackWithRiders("Ram", self, 7, std::vector<Die>{{1, 12}}, 4, DamageType::Bludgeoning, 1, std::move(ramRiders));

      // Bite: +7, 2d6+4 Piercing, reach 5 ft. (the against-Prone-target 4d6+4 variant is not modelled).
      auto bite = self->addMeleeAttack("Bite", self, 7, std::vector<Die>{{2, 6}}, 4, DamageType::Piercing, 1);

      // Claw: +7, 1d6+4 Slashing, reach 5 ft.
      auto claw = self->addMeleeAttack("Claw", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Slashing, 1);

      // Opportunity attack uses the same Claw. Fire Breath (a recharge breath weapon) is not ported and omitted.
      self->addReactionAttack("Claw", self, 7, std::vector<Die>{{1, 6}}, 4, DamageType::Slashing, 1);

      // Three distinct attacks (Ram, Bite, Claw) used once each in any order.
      self->addAttackTransition(ram.get(), AttackFsm::START, 1);
      self->addAttackTransition(bite.get(), AttackFsm::START, 2);
      self->addAttackTransition(claw.get(), AttackFsm::START, 3);
      self->addAttackTransition(bite.get(), 1, 4);
      self->addAttackTransition(claw.get(), 1, 5);
      self->addAttackTransition(ram.get(), 2, 6);
      self->addAttackTransition(claw.get(), 2, 7);
      self->addAttackTransition(ram.get(), 3, 8);
      self->addAttackTransition(bite.get(), 3, 9);
      self->addAttackTransition(claw.get(), 4, AttackFsm::NOP);
      self->addAttackTransition(bite.get(), 5, AttackFsm::NOP);
      self->addAttackTransition(claw.get(), 6, AttackFsm::NOP);
      self->addAttackTransition(ram.get(), 7, AttackFsm::NOP);
      self->addAttackTransition(bite.get(), 8, AttackFsm::NOP);
      self->addAttackTransition(ram.get(), 9, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 4);
      self->setSavingThrow(SavingThrow::DEX, 0);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 2);
      self->setSavingThrow(SavingThrow::CHA, 0);
      self->setAthletics(4);
      self->setAcrobatics(0);
      self->setPassivePerception(18);
    }
  }

  // HP 114 (12d10 + 48), AC 14, Speed 30 ft. (Fly 60 ft.), Initiative +0.
  Chimera::Chimera(int num)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, concatName(std::string(_className), num), 114, 14, 0, 0, 60, 0)
  {
    _instanceId = generateInstanceId();
    buildChimera(this);
  }

  Chimera::Chimera(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, name, 114, 14, 0, 0, 60, 0)
  {
    _instanceId = generateInstanceId();
    buildChimera(this);
  }
}
