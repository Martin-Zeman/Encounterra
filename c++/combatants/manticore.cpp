#include "combatants/manticore.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildManticore(Manticore *self)
    {
      self->setSize(Size::LARGE);

      // Multiattack: three attacks, using Rend or Tail Spike in any combination.
      // Rend: +5, 1d8+3 Slashing, reach 5 ft.
      // Tail Spike: +5, 1d8+3 Piercing, range 100/200 ft. (long range = 40 cells). Its finite spike supply is
      // not modelled (treated as unlimited ammo).
      auto rend = self->addMeleeAttack("Rend", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);
      auto spike = self->addRangedAttack("Tail Spike", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 40);
      self->addReactionAttack("Rend", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(spike.get()));

      // Three attacks, any combination of Rend (R) or Tail Spike (S).
      self->addAttackTransition(rend.get(), AttackFsm::START, 1);
      self->addAttackTransition(spike.get(), AttackFsm::START, 2);
      self->addAttackTransition(rend.get(), 1, 3);
      self->addAttackTransition(spike.get(), 1, 4);
      self->addAttackTransition(rend.get(), 2, 5);
      self->addAttackTransition(spike.get(), 2, 6);
      self->addAttackTransition(rend.get(), 3, AttackFsm::NOP);
      self->addAttackTransition(spike.get(), 3, AttackFsm::NOP);
      self->addAttackTransition(rend.get(), 4, AttackFsm::NOP);
      self->addAttackTransition(spike.get(), 4, AttackFsm::NOP);
      self->addAttackTransition(rend.get(), 5, AttackFsm::NOP);
      self->addAttackTransition(spike.get(), 5, AttackFsm::NOP);
      self->addAttackTransition(rend.get(), 6, AttackFsm::NOP);
      self->addAttackTransition(spike.get(), 6, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, 3);
      self->setSavingThrow(SavingThrow::CON, 3);
      self->setSavingThrow(SavingThrow::INT, -2);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -1);
      self->setAthletics(3);
      self->setAcrobatics(3);
      self->setPassivePerception(11);
    }
  }

  // HP 68 (8d10 + 24), AC 14, Speed 30 ft. (Fly 50 ft.), Initiative +3.
  Manticore::Manticore(int num)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, concatName(std::string(_className), num), 68, 14, 3, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildManticore(this);
  }

  Manticore::Manticore(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, name, 68, 14, 3, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildManticore(this);
  }
}
