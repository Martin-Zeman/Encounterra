#include "combatants/owlbear.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildOwlbear(Owlbear *self)
    {
      self->setSize(Size::LARGE);

      // Multiattack: the owlbear makes two Rend attacks. Rend: +7, 2d8+5 Slashing, reach 5 ft.
      auto rend = self->addMeleeAttack("Rend", self, 7, std::vector<Die>{{2, 8}}, 5, DamageType::Slashing, 1);
      self->addReactionAttack("Rend", self, 7, std::vector<Die>{{2, 8}}, 5, DamageType::Slashing, 1);

      // Two identical Rend attacks: 0 -> 1 -> nop.
      self->addAttackTransition(rend.get(), AttackFsm::START, 1);
      self->addAttackTransition(rend.get(), 1, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 5);
      self->setSavingThrow(SavingThrow::DEX, 1);
      self->setSavingThrow(SavingThrow::CON, 3);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -2);
      self->setAthletics(5);
      self->setAcrobatics(1);
      self->setPassivePerception(15);
    }
  }

  // HP 59 (7d10 + 21), AC 13, Speed 40 ft. (Climb 40 ft.), Initiative +1.
  Owlbear::Owlbear(int num)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, concatName(std::string(_className), num), 59, 13, 1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildOwlbear(this);
  }

  Owlbear::Owlbear(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::MONSTROSITY, _classLevel, name, 59, 13, 1, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildOwlbear(this);
  }
}
