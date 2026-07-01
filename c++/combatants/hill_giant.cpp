#include "combatants/hill_giant.hpp"
#include "abilities/on_hit_prone.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildHillGiant(HillGiant *self)
    {
      self->setSize(Size::HUGE);

      // Multiattack: two attacks, using Tree Club or Trash Lob in any combination.
      // Tree Club: +8, 3d8+5 Bludgeoning, reach 10 ft. On a hit a Large or smaller target has the Prone
      // condition (no save, 2024 statblock).
      std::vector<std::unique_ptr<OnHit>> clubRiders;
      clubRiders.push_back(std::make_unique<OnHitProne>(Size::LARGE));
      auto club = self->addMeleeAttackWithRiders("Tree Club", self, 8, std::vector<Die>{{3, 8}}, 5, DamageType::Bludgeoning, 2,
                                                 std::move(clubRiders));

      // Trash Lob: +8, 2d10+5 Bludgeoning, range 60/240 ft. (long range = 48 cells). Its Poisoned rider (DC 15
      // Con save) has no engine model and is omitted.
      auto lob = self->addRangedAttack("Trash Lob", self, 8, std::vector<Die>{{2, 10}}, 5, DamageType::Bludgeoning, 48);

      // Opportunity attack uses the same Tree Club (no Prone rider on the reaction).
      self->addReactionAttack("Tree Club", self, 8, std::vector<Die>{{3, 8}}, 5, DamageType::Bludgeoning, 2);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(lob.get()));

      // Two attacks, any combination of Tree Club (C) or Trash Lob (L).
      self->addAttackTransition(club.get(), AttackFsm::START, 1);
      self->addAttackTransition(lob.get(), AttackFsm::START, 2);
      self->addAttackTransition(club.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(lob.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(club.get(), 2, AttackFsm::NOP);
      self->addAttackTransition(lob.get(), 2, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 5);
      self->setSavingThrow(SavingThrow::DEX, -1);
      self->setSavingThrow(SavingThrow::CON, 4);
      self->setSavingThrow(SavingThrow::INT, -3);
      self->setSavingThrow(SavingThrow::WIS, -1);
      self->setSavingThrow(SavingThrow::CHA, -2);
      self->setAthletics(5);
      self->setAcrobatics(-1);
      self->setPassivePerception(12);
    }
  }

  // HP 105 (10d12 + 40), AC 13, Speed 40 ft., Initiative +2.
  HillGiant::HillGiant(int num)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 105, 13, 2, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildHillGiant(this);
  }

  HillGiant::HillGiant(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 105, 13, 2, 0, 40, 0)
  {
    _instanceId = generateInstanceId();
    buildHillGiant(this);
  }
}
