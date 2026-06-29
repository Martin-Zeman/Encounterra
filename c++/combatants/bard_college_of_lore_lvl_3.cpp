#include "combatants/bard_college_of_lore_lvl_3.hpp"
#include "core/misc.hpp"
#include "core/utils.hpp"

namespace enc
{
  namespace
  {
    void configureBardCollegeOfLoreLvl3(BardCollegeOfLoreLvl3 *self)
    {
      // A finesse rapier wielded with the bard's Dexterity (+2): +4 to hit, 1d8+2 piercing.
      auto rapier = self->addMeleeAttack("Rapier", self, 4, std::vector<Die>{{1, 8}}, 2, DamageType::Piercing, 1);
      self->addReactionAttack("Rapier", self, 4, std::vector<Die>{{1, 8}}, 2, DamageType::Piercing, 1);

      self->addSpellSlots();

      // Cantrip
      self->addViciousMockery();
      // Leveled spells (4x L1, 2x L2 slots at bard level 3)
      self->addBane();
      self->addCharmPerson();
      self->addColorSpray();
      self->addDissonantWhispers();
      self->addHealingWord();

      // College of Lore features
      self->addBardicInspiration();
      self->addCuttingWords();

      self->setSavingThrow(SavingThrow::STR, 0);
      self->setSavingThrow(SavingThrow::DEX, 4);
      self->setSavingThrow(SavingThrow::CON, 1);
      self->setSavingThrow(SavingThrow::INT, 0);
      self->setSavingThrow(SavingThrow::WIS, 1);
      self->setSavingThrow(SavingThrow::CHA, 5);
      self->setAthletics(0);
      self->setAcrobatics(4);

      self->addAttackTransition(rapier.get(), AttackFsm::START, AttackFsm::NOP);
    }
  }

  BardCollegeOfLoreLvl3::BardCollegeOfLoreLvl3(int num)
      : Combatant(CombatantType::BARD, Bard::COLLEGE_OF_LORE, _classLevel, concatName(std::string(_className), num), 24, 13, 2, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureBardCollegeOfLoreLvl3(this);
  }

  BardCollegeOfLoreLvl3::BardCollegeOfLoreLvl3(const std::string &name)
      : Combatant(CombatantType::BARD, Bard::COLLEGE_OF_LORE, _classLevel, name, 24, 13, 2, 5, 30, 13)
  {
    _instanceId = generateInstanceId();
    configureBardCollegeOfLoreLvl3(this);
  }
}
