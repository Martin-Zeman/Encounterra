#include "combatants/tiger.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildTiger(Tiger *self)
    {
      self->setSize(Size::LARGE);

      // Pounce: +5, 1d6+3 Slashing, reach 5 ft. The 2024 Multiattack is "one Pounce attack and uses Prowl";
      // Prowl is a move-and-Hide rider with no combat-simulation infrastructure, so the Tiger makes a single
      // Pounce per turn. The advantage-conditional extra damage and Prone rider are likewise omitted.
      auto pounce = self->addMeleeAttack("Pounce", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1);

      self->addReactionAttack("Pounce", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1);

      self->addAttackTransition(pounce.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, 3);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -1);
      self->setAthletics(3);
      self->setAcrobatics(3);
    }
  }

  Tiger::Tiger(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 22, 13, 3, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildTiger(this);
  }

  Tiger::Tiger(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 22, 13, 3, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildTiger(this);
  }
}
