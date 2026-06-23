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

      // Multiattack (2024): the tiger makes one Pounce attack and uses Prowl. Prowl is a move-and-Hide rider
      // with no combat-simulation infrastructure, so the tiger's whole action is the Pounce.
      //
      // Pounce ports the Python ability (simulator/abilities/pounce.py): the tiger charges `distance` cells in
      // a straight line, makes a primary claw attack (+5, 1d6+3 Slashing) that knocks a Large-or-smaller target
      // Prone on a failed DC 13 Strength save, and follows up with a Bite (+5, 1d8+3 Piercing) if the target is
      // left Prone. The primary/secondary attacks are "suppressed" (owned by the Pounce, not independently
      // plannable).
      std::vector<std::unique_ptr<OnHit>> proneRider;
      proneRider.push_back(std::make_unique<OnHitProne>(SavingThrow::STR, 13));
      auto claws = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", "Pounce", self, AbilityType::MELEE_ATTACK, 5,
                                                        std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1, 1, Uses(), std::move(proneRider));
      auto bite = std::make_shared<MeleeAttackFactory>("MeleeAttackFactory", "Bite", self, AbilityType::MELEE_ATTACK, 5, std::vector<Die>{{1, 8}}, 3,
                                                       DamageType::Piercing, 1);

      self->addPounce(claws, bite, 4);

      self->addReactionAttack("Claws", self, 5, std::vector<Die>{{1, 6}}, 3, DamageType::Slashing, 1);

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
