#include "combatants/brown_bear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{

  namespace
  {
    void buildBrownBear(BrownBear *self)
    {
      self->setSize(Size::LARGE);

      auto bite = self->addMeleeAttack("Bite", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Piercing, 1);
      auto claw = self->addMeleeAttack("Claw", self, 5, std::vector<Die>{{1, 4}}, 3, DamageType::Slashing, 1);
      self->addReactionAttack("Claw", self, 5, std::vector<Die>{{1, 4}}, 3, DamageType::Slashing, 1);

      // Multiattack: the bear makes one Bite attack and one Claw attack. The attack FSM grants the second attack of
      // the pair once the first is spent: Bite (0->1) then Claw (1->nop), or Claw (0->2) then Bite (2->nop).
      self->addAttackTransition(bite.get(), AttackFsm::START, 1);
      self->addAttackTransition(claw.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(claw.get(), AttackFsm::START, 2);
      self->addAttackTransition(bite.get(), 2, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -2);
      self->setAthletics(3);
      self->setAcrobatics(1);
    }
  }

  BrownBear::BrownBear(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 22, 11, 1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildBrownBear(this);
  }

  BrownBear::BrownBear(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 22, 11, 1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildBrownBear(this);
  }
}
