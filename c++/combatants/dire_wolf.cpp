#include "combatants/dire_wolf.hpp"
#include "abilities/on_hit_prone.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildDireWolf(DireWolf *self)
    {
      self->setSize(Size::LARGE);

      // Bite: +5, 1d10+3 Piercing, reach 5 ft. On a hit the target has the Prone condition if it is Huge or
      // smaller — no saving throw (2024 statblock).
      std::vector<std::unique_ptr<OnHit>> biteRiders;
      biteRiders.push_back(std::make_unique<OnHitProne>(Size::HUGE));
      auto bite = self->addMeleeAttackWithRiders("Bite", self, 5, std::vector<Die>{{1, 10}}, 3, DamageType::Piercing, 1, std::move(biteRiders));

      // Opportunity attack uses the same Bite (no Prone rider on the reaction, mirroring the Python reaction bite).
      self->addReactionAttack("Bite", self, 5, std::vector<Die>{{1, 10}}, 3, DamageType::Piercing, 1);

      // Single attack: 0 -> nop.
      self->addAttackTransition(bite.get(), AttackFsm::START, AttackFsm::NOP);

      // Pack Tactics: the Dire Wolf has Advantage on attack rolls against a target if at least one of its allies
      // is within 5 ft of that target.
      self->addPackTactics();

      self->setSavingThrow(SavingThrow::STR, 3);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 2);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, -2);
      self->setAthletics(3);
      self->setAcrobatics(2);
    }
  }

  DireWolf::DireWolf(int num)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, concatName(std::string(_className), num), 22, 14, 2, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildDireWolf(this);
  }

  DireWolf::DireWolf(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::BEAST, _classLevel, name, 22, 14, 2, 0, 50, 0)
  {
    _instanceId = generateInstanceId();
    buildDireWolf(this);
  }
}
