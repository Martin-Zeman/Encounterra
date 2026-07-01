#include "combatants/stone_giant.hpp"
#include "abilities/on_hit_prone.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildStoneGiant(StoneGiant *self)
    {
      self->setSize(Size::HUGE);

      // Multiattack: two attacks, using Stone Club or Boulder in any combination.
      // Stone Club: +9, 3d10+6 Bludgeoning, reach 15 ft.
      auto club = self->addMeleeAttack("Stone Club", self, 9, std::vector<Die>{{3, 10}}, 6, DamageType::Bludgeoning, 3);

      // Boulder: +9, 2d8+6 Bludgeoning, range 60/240 ft. (long range = 48 cells). On a hit a Large or smaller
      // target has the Prone condition (no save, 2024 statblock).
      std::vector<std::unique_ptr<OnHit>> boulderRiders;
      boulderRiders.push_back(std::make_unique<OnHitProne>(Size::LARGE));
      auto boulder = self->addRangedAttackWithRiders("Boulder", self, 9, std::vector<Die>{{2, 8}}, 6, DamageType::Bludgeoning, 48,
                                                     std::move(boulderRiders));

      // Opportunity attack uses the same Stone Club.
      self->addReactionAttack("Stone Club", self, 9, std::vector<Die>{{3, 10}}, 6, DamageType::Bludgeoning, 3);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(boulder.get()));

      // Deflect Missile (reaction that reduces ranged weapon damage) has no engine model and is omitted.

      // Two attacks, any combination of Stone Club (C) or Boulder (B).
      self->addAttackTransition(club.get(), AttackFsm::START, 1);
      self->addAttackTransition(boulder.get(), AttackFsm::START, 2);
      self->addAttackTransition(club.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(boulder.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(club.get(), 2, AttackFsm::NOP);
      self->addAttackTransition(boulder.get(), 2, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 6);
      self->setSavingThrow(SavingThrow::DEX, 5);
      self->setSavingThrow(SavingThrow::CON, 8);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 4);
      self->setSavingThrow(SavingThrow::CHA, -1);
      self->setAthletics(12);
      self->setAcrobatics(2);
      self->setStealth(5);
      self->setPassivePerception(14);
    }
  }

  // HP 126 (11d12 + 55), AC 17, Speed 40 ft., Initiative +5.
  StoneGiant::StoneGiant(int num)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 126, 17, 5, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildStoneGiant(this);
  }

  StoneGiant::StoneGiant(const std::string &name) : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 126, 17, 5, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildStoneGiant(this);
  }
}