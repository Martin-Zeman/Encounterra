#include "combatants/frost_giant.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildFrostGiant(FrostGiant *self)
    {
      self->setSize(Size::HUGE);

      // Multiattack: two attacks, using Frost Axe or Great Bow in any combination.
      // Frost Axe: +9, 2d12+6 Slashing plus 2d8 Cold, reach 10 ft.
      auto axe = self->addMeleeAttackWithRiders("Frost Axe", self, 9, std::vector<Die>{{2, 12}}, 6, DamageType::Slashing, 2,
                                                std::vector<std::unique_ptr<OnHit>>{},
                                                std::vector<DmgDieWithType>{{{2, 8}, DamageType::Cold}});

      // Great Bow: +9, 2d10+6 Piercing plus 2d6 Cold, range 150/600 ft. (long range = 120 cells). The speed
      // reduction rider has no engine model and is omitted.
      auto bow = self->addRangedAttackWithRiders("Great Bow", self, 9, std::vector<Die>{{2, 10}}, 6, DamageType::Piercing, 120,
                                                 std::vector<std::unique_ptr<OnHit>>{},
                                                 std::vector<DmgDieWithType>{{{2, 6}, DamageType::Cold}});

      // Opportunity attack uses the same Frost Axe.
      self->addReactionAttack("Frost Axe", self, 9, std::vector<Die>{{2, 12}}, 6, DamageType::Slashing, 2);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(bow.get()));

      // War Cry (bonus action, grants allies advantage) has no engine model and is omitted.

      // Two attacks, any combination of Frost Axe (A) or Great Bow (B).
      self->addAttackTransition(axe.get(), AttackFsm::START, 1);
      self->addAttackTransition(bow.get(), AttackFsm::START, 2);
      self->addAttackTransition(axe.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(bow.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(axe.get(), 2, AttackFsm::NOP);
      self->addAttackTransition(bow.get(), 2, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 6);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 8);
      self->setSavingThrow(SavingThrow::INT, -1);
      self->setSavingThrow(SavingThrow::WIS, 3);
      self->setSavingThrow(SavingThrow::CHA, 4);
      self->setAthletics(9);
      self->setAcrobatics(-1);
      self->setPassivePerception(13);
    }
  }

  // HP 149 (13d12 + 65), AC 15, Speed 40 ft., Initiative +2. Immune to Cold damage.
  FrostGiant::FrostGiant(int num)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 149, 15, 2, 0, 40, 0, {},
                  {DamageType::Cold})
  {
    _instanceId = generateInstanceId();
    buildFrostGiant(this);
  }

  FrostGiant::FrostGiant(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 149, 15, 2, 0, 40, 0, {}, {DamageType::Cold})
  {
    _instanceId = generateInstanceId();
    buildFrostGiant(this);
  }
}
