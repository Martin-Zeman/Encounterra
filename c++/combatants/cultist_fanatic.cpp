#include "combatants/cultist_fanatic.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void buildCultistFanatic(CultistFanatic *self)
    {
      // Spellcasting: the Fanatic is modelled as a Cleric-3 slot pool (two level-2 slots) so it can cast
      // Hold Person (level 2). Command, Spiritual Weapon, Light and Thaumaturgy are omitted.
      self->addSpellSlots(CombatantType::CLERIC, 3);
      self->addHoldPerson();

      // Pact Blade: +4, 1d8+2 Slashing plus 2d6 Necrotic, reach 5 ft.
      auto blade = self->addMeleeAttackWithRiders("Pact Blade", self, 4, std::vector<Die>{{1, 8}}, 2, DamageType::Slashing, 1,
                                                  std::vector<std::unique_ptr<OnHit>>{},
                                                  std::vector<DmgDieWithType>{{{2, 6}, DamageType::Necrotic}});

      self->addReactionAttack("Pact Blade", self, 4, std::vector<Die>{{1, 8}}, 2, DamageType::Slashing, 1);

      // Single attack: 0 -> nop.
      self->addAttackTransition(blade.get(), AttackFsm::START, AttackFsm::NOP);

      self->setSavingThrow(SavingThrow::STR, 0);
      self->setSavingThrow(SavingThrow::DEX, 2);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 4);
      self->setSavingThrow(SavingThrow::CHA, 1);
      self->setAthletics(0);
      self->setAcrobatics(2);
      self->setPassivePerception(12);
    }
  }

  // HP 44 (8d8 + 8), AC 13, Speed 30 ft., Initiative +2. Spell attack +4, spell save DC 12.
  CultistFanatic::CultistFanatic(int num)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, concatName(std::string(_className), num), 44, 13, 2, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildCultistFanatic(this);
  }

  CultistFanatic::CultistFanatic(const std::string &name)
      : Combatant(CombatantType::MONSTER, Monster::HUMANOID, _classLevel, name, 44, 13, 2, 4, 30, 12)
  {
    _instanceId = generateInstanceId();
    buildCultistFanatic(this);
  }
}
