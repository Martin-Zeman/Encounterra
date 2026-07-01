#include "combatants/zombie.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildZombie(Zombie *self)
    {
      // Slam: +3, 1d6+1 Bludgeoning, reach 5 ft. The Zombie makes a single Slam attack (no multiattack).
      auto slam = self->addMeleeAttack("Slam", self, 3, std::vector<Die>{{1, 6}}, 1, DamageType::Bludgeoning, 1);
      self->addReactionAttack("Slam", self, 3, std::vector<Die>{{1, 6}}, 1, DamageType::Bludgeoning, 1);

      // Undead Fortitude: if damage (that is not Radiant or from a Critical Hit) would drop it to 0 HP, it makes
      // a Constitution save (DC 5 + damage taken) to drop to 1 HP instead. Handled by the resolver.
      self->addUndeadFortitude();

      // Single attack: 0 -> nop.
      self->addAttackTransition(slam.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 1);
      self->setSavingThrow(SavingThrow::DEX, -2);
      self->setSavingThrow(SavingThrow::CON, 3);
      self->setSavingThrow(SavingThrow::INT, -4);
      self->setSavingThrow(SavingThrow::WIS, 0);
      self->setSavingThrow(SavingThrow::CHA, -3);
      self->setAthletics(1);
      self->setAcrobatics(-2);
      self->setStealth(-2);
      self->setPassivePerception(8);
    }
  }

  // HP 15 (2d8 + 6), AC 8, Speed 20 ft., Initiative -2. Poison immunity + Poisoned condition immunity are set in
  // the constructor. The Exhaustion condition immunity is not modelled (Exhaustion is not tracked by the engine).
  Zombie::Zombie(int num)
      : Combatant(CombatantType::MONSTER, Monster::UNDEAD, _classLevel, concatName(std::string(_className), num), 15, 8, -2, 0, 20, 0, {},
                  {DamageType::Poison}, {}, Conditions::POISONED)
  {
    _instanceId = generateInstanceId();
    buildZombie(this);
  }

  Zombie::Zombie(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::UNDEAD, _classLevel, name, 15, 8, -2, 0, 20, 0, {}, {DamageType::Poison}, {}, Conditions::POISONED)
  {
    _instanceId = generateInstanceId();
    buildZombie(this);
  }
}
