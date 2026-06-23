#include "combatants/lion.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildLion(Lion *self)
    {
      self->setSize(Size::LARGE);

      // Multiattack: the lion makes two Rend attacks; RAW it may replace one Rend with a use of Roar.
      // Rend: +5, 1d8+3 Slashing, reach 5 ft.
      auto rend = self->addMeleeAttack("Rend", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);

      self->addReactionAttack("Rend", self, 5, std::vector<Die>{{1, 8}}, 3, DamageType::Slashing, 1);

      // Two identical Rend attacks: 0 -> 1 -> nop.
      self->addAttackTransition(rend.get(), AttackFsm::START, 1);
      self->addAttackTransition(rend.get(), 1, AttackFsm::NOP);

      // Roar: each enemy within 15 ft (3 cells) makes a DC 11 Wisdom save or is Frightened until the start of
      // the lion's next turn. "Replace one attack with Roar" is approximated as a standalone Action option
      // (the planner picks Roar or the two-Rend multiattack). The mechanical consequences of Frightened are
      // not yet modelled, so Roar's threat is a heuristic for the debuff. Pack Tactics and Running Leap are
      // omitted.
      self->addRoar(11, 3);

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 0);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -1);
      self->setAthletics(3);
      self->setAcrobatics(2);
    }
  }

  Lion::Lion(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 22, 12, 2, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildLion(this);
  }

  Lion::Lion(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 22, 12, 2, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildLion(this);
  }
}
