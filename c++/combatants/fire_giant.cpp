#include "combatants/fire_giant.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildFireGiant(FireGiant *self)
    {
      self->setSize(Size::HUGE);

      // Multiattack: two attacks, using Flame Sword or Hammer Throw in any combination.
      // Flame Sword: +11, 4d6+7 Slashing plus 3d6 Fire, reach 10 ft.
      auto sword = self->addMeleeAttackWithRiders("Flame Sword", self, 11, std::vector<Die>{{4, 6}}, 7, DamageType::Slashing, 2,
                                                  std::vector<std::unique_ptr<OnHit>>{},
                                                  std::vector<DmgDieWithType>{{{3, 6}, DamageType::Fire}});

      // Hammer Throw: +11, 3d10+7 Bludgeoning plus 1d8 Fire, range 60/240 ft. (long range = 48 cells). The push
      // and attack-disadvantage rider has no engine model and is omitted.
      auto hammer = self->addRangedAttackWithRiders("Hammer Throw", self, 11, std::vector<Die>{{3, 10}}, 7, DamageType::Bludgeoning, 48,
                                                    std::vector<std::unique_ptr<OnHit>>{},
                                                    std::vector<DmgDieWithType>{{{1, 8}, DamageType::Fire}});

      // Opportunity attack uses the same Flame Sword.
      self->addReactionAttack("Flame Sword", self, 11, std::vector<Die>{{4, 6}}, 7, DamageType::Slashing, 2);

      self->setDangerZoneAttack(static_cast<DirectThreatFactory *>(hammer.get()));

      // Two attacks, any combination of Flame Sword (S) or Hammer Throw (H).
      self->addAttackTransition(sword.get(), AttackFsm::START, 1);
      self->addAttackTransition(hammer.get(), AttackFsm::START, 2);
      self->addAttackTransition(sword.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(hammer.get(), 1, AttackFsm::NOP);
      self->addAttackTransition(sword.get(), 2, AttackFsm::NOP);
      self->addAttackTransition(hammer.get(), 2, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 7);
      self->setSavingThrow(SavingThrow::DEX, 3);
      self->setSavingThrow(SavingThrow::CON, 10);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 2);
      self->setSavingThrow(SavingThrow::CHA, 5);
      self->setAthletics(11);
      self->setAcrobatics(3);
      self->setPassivePerception(16);
    }
  }

  // HP 162 (13d12 + 78), AC 18, Speed 30 ft., Initiative +3. Immune to Fire damage.
  FireGiant::FireGiant(int num)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, concatName(std::string(_className), num), 162, 18, 3, 0, 30, 0, {},
                  {DamageType::Fire})
  {
    _instanceId = generateInstanceId();
    buildFireGiant(this);
  }

  FireGiant::FireGiant(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::GIANT, _classLevel, name, 162, 18, 3, 0, 30, 0, {}, {DamageType::Fire})
  {
    _instanceId = generateInstanceId();
    buildFireGiant(this);
  }
}
